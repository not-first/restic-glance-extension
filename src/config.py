import logging
import os
from src.types import RepoConfig

logger = logging.getLogger("restic-api")

VALID_STATS_MODES = {"repository-size", "latest-snapshot"}


class ConfigurationError(Exception):
    # raised when configuration is invalid

    pass


# application configuration loaded from environment variables
class Config:
    CACHE_INTERVAL: int
    REPOS: list[str]
    REPOS_BASE_PATH: str
    STATS_MODE: str
    RESTIC_CONFIG: dict[str, RepoConfig]

    def __init__(self) -> None:
        # initialize configuration from environment variables
        # load cache interval
        try:
            self.CACHE_INTERVAL = int(os.getenv("RESTIC_CACHE_INTERVAL", "3600"))
        except ValueError:
            raise ConfigurationError("RESTIC_CACHE_INTERVAL must be a valid integer")

        # load repos list
        repos_env = os.getenv("RESTIC_REPOS", "").strip()
        if not repos_env:
            raise ConfigurationError(
                "RESTIC_REPOS environment variable is required and cannot be empty"
            )

        self.REPOS = [repo.strip() for repo in repos_env.split(",") if repo.strip()]
        if not self.REPOS:
            raise ConfigurationError(
                "RESTIC_REPOS must contain at least one repository alias"
            )

        # load base path and mode
        self.REPOS_BASE_PATH = os.getenv("RESTIC_REPOS_BASE_PATH", "/app/repos").rstrip(
            "/"
        )
        self.STATS_MODE = os.getenv("RESTIC_STATS_MODE", "repository-size")

        # validate stats mode
        if self.STATS_MODE not in VALID_STATS_MODES:
            raise ConfigurationError(
                f"RESTIC_STATS_MODE must be one of {VALID_STATS_MODES}, got '{self.STATS_MODE}'"
            )

        # load repo configurations
        self.RESTIC_CONFIG = {}
        for repo in self.REPOS:
            repo_key = repo.upper().replace("-", "_")
            password = os.getenv(f"{repo_key}_RESTIC_PASSWORD")

            if not password:
                raise ConfigurationError(
                    f"Missing required password for repo '{repo}': "
                    f"{repo_key}_RESTIC_PASSWORD environment variable not set"
                )

            repo_config: RepoConfig = {
                "password": password,
                "env": {},
                "url": os.getenv(
                    f"{repo_key}_RESTIC_URL", f"{self.REPOS_BASE_PATH}/{repo}"
                ),
            }

            # collect custom environment variables
            env_var_prefix = f"{repo_key}_RESTIC_ENV__"
            for k, v in os.environ.items():
                if not k.startswith(env_var_prefix):
                    continue
                repo_config["env"][k[len(env_var_prefix) :]] = v

            # check for per-repo stats mode override
            repo_stats_mode = os.getenv(f"{repo_key}_RESTIC_STATS_MODE")
            if repo_stats_mode:
                if repo_stats_mode not in VALID_STATS_MODES:
                    raise ConfigurationError(
                        f"Invalid stats mode for repo '{repo}': {repo_key}_RESTIC_STATS_MODE "
                        f"must be one of {VALID_STATS_MODES}, got '{repo_stats_mode}'"
                    )
                repo_config["stats_mode"] = repo_stats_mode
                logger.info(f"using stats mode '{repo_stats_mode}' for repo: {repo}")

            self.RESTIC_CONFIG[repo] = repo_config
            logger.info(f"configured repository: {repo} -> {repo_config['url']}")

    def validate(self) -> None:
        # validate configuration is complete and correct
        if self.CACHE_INTERVAL <= 0:
            raise ConfigurationError("RESTIC_CACHE_INTERVAL must be positive")

        logger.info(
            f"configuration validated: {len(self.RESTIC_CONFIG)} repositories, "
            f"{self.CACHE_INTERVAL}s cache interval, mode={self.STATS_MODE}"
        )


config = Config()
config.validate()
