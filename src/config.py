import os

class Config:
    CACHE_INTERVAL = int(os.getenv("CACHE_INTERVAL", 3600))
    ENABLE_AUTORESTIC_ICON = os.getenv("ENABLE_AUTORESTIC_ICON", "false").lower() == "true"
    REPOS = os.getenv("REPOS", "").split(",")
    RESTIC_CONFIG = {
        repo: {
            "path": os.getenv(f"{repo.upper().replace('-', '_')}_RESTIC_REPO"),
            "password": os.getenv(f"{repo.upper().replace('-', '_')}_RESTIC_PASSWORD")
        }
        for repo in REPOS
    }

config = Config()