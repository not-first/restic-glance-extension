import logging
import threading
import time
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from src.config import config
from src.restic import ResticRepo
from datetime import datetime, timezone
from dateutil.parser import isoparse
import humanize

uvicorn_logger = logging.getLogger("uvicorn.error")
logging.basicConfig(format="%(levelname)s:    %(message)s", level=uvicorn_logger.getEffectiveLevel())
logger = logging.getLogger("restic-api")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Restic API is running!"}

# Simply in memory cache for restic repo info
repos = {}
cache = {}

def update_cache():
    logger.info("Fetching initial cache for all repos")
    for repo_alias, repo_config in config.RESTIC_CONFIG.items():
        repos[repo_alias] = ResticRepo(repo_config)
        cache[repo_alias] = repos[repo_alias].get_backup_info()

    while True:
        time.sleep(config.CACHE_INTERVAL)
        logger.info("Updating cache for all repos")
        for repo_alias, repo in repos.items():
            cache[repo_alias] = repo.get_backup_info()

@app.get("/{repo}")
async def get_backups(repo: str, request: Request):
    limit = int(request.query_params.get("limit", 1))
    data = cache.get(repo, {"error": f"No cache available for repo '{repo}'."})
    if "error" in data:
        return HTMLResponse(
            content=f"<p class='color-negative'>Error: {data['error']}</p>",
            headers={"Widget-Title": "Backups", "Widget-Content-Type": "html"}
        )

    snaps = data.get("all_snapshots", [])[:limit]
    for s in snaps:
        # Make sure to use short_id for consistency
        s["id"] = s.get("short_id", "")
        dt = isoparse(s["time"])
        s["readable_time"] = humanize.naturaltime(datetime.now(timezone.utc) - dt)

    if request.query_params.get("autorestic-icon", "false").lower() == "true":
        for s in snaps:
            tags = s.get("tags", [])
            s["method"] = "cron" if "ar:cron" in tags else "manual"

    data["latest_snapshot"] = snaps[0] if snaps else {}
    data["other_snapshots"] = snaps[1:] if len(snaps) > 1 else []

    # Add hide-file-count parameter
    data["hide_file_count"] = request.query_params.get("hide-file-count", "false").lower() == "true"

    from src.widget import parse_widget_html
    return HTMLResponse(
        content=parse_widget_html(data),
        headers={"Widget-Title": "Backups", "Widget-Content-Type": "html"}
    )

def start_cache_thread():
    thread = threading.Thread(target=update_cache, daemon=True)
    thread.start()

start_cache_thread()
