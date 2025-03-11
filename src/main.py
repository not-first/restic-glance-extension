import logging
import threading
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.config import config
from src.restic import get_backup_info

logging.basicConfig(format="%(levelname)s:    %(message)s", level=logging.INFO)
logger = logging.getLogger("restic-api")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Restic API is running!"}

# Simply in memory cache for restic repo info
cache = {}

def update_cache():
    logger.info("Fetching initial cache for all repos")
    for repo, repo_config in config.RESTIC_CONFIG.items():
        cache[repo] = get_backup_info(repo_config["path"], repo_config["password"])

    while True:
        time.sleep(config.CACHE_INTERVAL)
        logger.info("Updating cache for all repos")
        for repo, repo_config in config.RESTIC_CONFIG.items():
            cache[repo] = get_backup_info(repo_config["path"], repo_config["password"])

@app.get("/{repo}")
async def get_backups(repo: str):
    data = cache.get(repo, {"error": f"No cache available for repo '{repo}'. Have you configured it properly?"})
    if "error" in data:
        return HTMLResponse(
            content=f"<p class='color-negative'>Error: {data['error']}</p>",
            headers={"Widget-Title": "Backups", "Widget-Content-Type": "html"}
        )
    from src.widget import parse_widget_html
    return HTMLResponse(
        content=parse_widget_html(data),
        headers={"Widget-Title": "Backups", "Widget-Content-Type": "html"}
    )

def start_cache_thread():
    thread = threading.Thread(target=update_cache, daemon=True)
    thread.start()

start_cache_thread()