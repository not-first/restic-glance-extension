import os


class Config:
    CACHE_INTERVAL = int(os.getenv("RESTIC_CACHE_INTERVAL", 3600))
    REPOS = os.getenv("RESTIC_REPOS", "").split(",")
    RESTIC_CONFIG = {
        repo: {
            "password": os.getenv(f"{repo.upper().replace('-', '_')}_RESTIC_PASSWORD")
        }
        for repo in REPOS
    }
    REPOS_BASE_PATH = os.getenv("RESTIC_REPOS_BASE_PATH", "app/repos").rstrip('/')


config = Config()
