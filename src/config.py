import os


class Config:
    CACHE_INTERVAL = int(os.getenv("RESTIC_CACHE_INTERVAL", 3600))
    REPOS = os.getenv("RESTIC_REPOS", "").split(",")
    REPOS_BASE_PATH = os.getenv("RESTIC_REPOS_BASE_PATH", "app/repos").rstrip('/')
    RESTIC_CONFIG = {}
    for repo in REPOS:
        repo_key = repo.upper().replace('-', '_')
        repo_config = {
            "password": os.getenv(f"{repo_key}_RESTIC_PASSWORD"),
            "env": {},
            "repo": os.getenv(f"{repo_key}_RESTIC_REPO", f"{REPOS_BASE_PATH}/{repo}")
        }

        env_var_prefix = f"{repo_key}_RESTIC_ENV__"
        for k, v in os.environ.items():
            if not k.startswith(env_var_prefix):
                continue
            repo_config["env"][k[len(env_var_prefix):]] = v
            
        RESTIC_CONFIG[repo] = repo_config
    print(RESTIC_CONFIG)


config = Config()
