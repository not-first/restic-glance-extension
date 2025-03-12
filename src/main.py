import logging
import threading
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from src.config import config
from src.restic import get_backup_info
from datetime import datetime, timezone
import humanize

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
        final_repo_path = f"/app/repos/{repo}"
        cache[repo] = get_backup_info(final_repo_path, repo_config["password"])

    while True:
        time.sleep(config.CACHE_INTERVAL)
        logger.info("Updating cache for all repos")
        for repo, repo_config in config.RESTIC_CONFIG.items():
            final_repo_path = f"/app/repos/{repo}"
            cache[repo] = get_backup_info(final_repo_path, repo_config["password"])

@app.get("/{repo}")
async def get_backups(repo: str, request: Request):
    data = cache.get(repo, {"error": f"No cache available for repo '{repo}'."})
    if "error" in data:
        return HTMLResponse(
            content=f"<p class='color-negative'>Error: {data['error']}</p>",
            headers={"Widget-Title": "Backups", "Widget-Content-Type": "html"}
        )

    snapshot_time_str = data["latest_snapshot"]["time"]
    dt = datetime.fromisoformat(snapshot_time_str.replace("Z", "+00:00"))
    data["latest_snapshot"]["readable_time"] = humanize.naturaltime(datetime.now(timezone.utc) - dt)

    # If autorestic-icon is "true", add a 'method' field based on tags
    if request.query_params.get("autorestic-icon", "false").lower() == "true":
        snap_tags = data["latest_snapshot"].get("tags", [])
        method_value = "cron" if "ar:cron" in snap_tags else "manual"
        data["latest_snapshot"]["method"] = method_value

    from src.widget import parse_widget_html
    return HTMLResponse(
        content=parse_widget_html(data),
        headers={"Widget-Title": "Backups", "Widget-Content-Type": "html"}
    )

def start_cache_thread():
    thread = threading.Thread(target=update_cache, daemon=True)
    thread.start()

start_cache_thread()