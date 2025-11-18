import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from src.config import config
from src.restic import ResticRepo
from src.service import format_backup_data
from src.types import BackupInfo
from src.widget import render_widget

# setup logging
uvicorn_logger = logging.getLogger("uvicorn.error")
logging.basicConfig(
    format="%(levelname)s:    %(message)s", level=uvicorn_logger.getEffectiveLevel()
)
logger = logging.getLogger("restic-api")

# in-memory cache for restic repo info
repos: dict[str, ResticRepo] = {}
cache: dict[str, BackupInfo | dict[str, str]] = {}
cache_task: asyncio.Task | None = None


# periodically update cache for all repos
async def update_cache_periodically() -> None:
    logger.info("starting initial cache fetch for all repos")

    # initial cache population
    for repo_alias, repo_config in config.RESTIC_CONFIG.items():
        repos[repo_alias] = ResticRepo(repo_config)
        try:
            # use per-repo stats mode if set, otherwise use global default
            stats_mode = repo_config.get("stats_mode", config.STATS_MODE)
            cache[repo_alias] = repos[repo_alias].get_backup_info(stats_mode)
            logger.info(f"initial cache populated for repo: {repo_alias}")
        except Exception as e:
            logger.error(f"failed to populate initial cache for repo {repo_alias}: {e}")
            cache[repo_alias] = {"error": f"failed to initialize: {str(e)}"}

    # periodic updates
    while True:
        await asyncio.sleep(config.CACHE_INTERVAL)
        logger.info("updating cache for all repos")

        for repo_alias, repo in repos.items():
            try:
                # use per-repo stats mode if set, otherwise use global default
                repo_config = config.RESTIC_CONFIG[repo_alias]
                stats_mode = repo_config.get("stats_mode", config.STATS_MODE)
                cache[repo_alias] = repo.get_backup_info(stats_mode)
                logger.debug(f"cache updated for repo: {repo_alias}")
            except Exception as e:
                logger.error(f"failed to update cache for repo {repo_alias}: {e}")
                cache[repo_alias] = {"error": f"cache update failed: {str(e)}"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # manage application lifespan events
    global cache_task

    # startup: start cache update task
    logger.info("starting application and cache update task")
    cache_task = asyncio.create_task(update_cache_periodically())

    yield

    # shutdown: cancel cache task
    logger.info("shutting down application")
    if cache_task:
        cache_task.cancel()
        try:
            await cache_task
        except asyncio.CancelledError:
            logger.info("cache update task cancelled successfully")


app = FastAPI(lifespan=lifespan)


# root endpoint for health check
@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "restic api is running!"}


# get backup widget html for a specific repository
@app.get("/{repo}")
async def get_backups(repo: str, request: Request) -> HTMLResponse:
    if repo not in config.RESTIC_CONFIG:
        available_repos = ", ".join(config.RESTIC_CONFIG.keys())
        logger.warning(f"request for unknown repo: {repo}")
        return HTMLResponse(
            content=f"<p class='color-negative'>error: repository '{repo}' not found. "
            f"available repositories: {available_repos}</p>",
            status_code=404,
            headers={"Widget-Title": "backups", "Widget-Content-Type": "html"},
        )

    # get data from cache
    data = cache.get(repo)
    if not data:
        logger.warning(f"no cache available for repo: {repo}")
        return HTMLResponse(
            content="<p class='color-negative'>error: cache not yet initialized. please wait.</p>",
            status_code=503,
            headers={"Widget-Title": "backups", "Widget-Content-Type": "html"},
        )

    # check for errors in cached data
    if "error" in data:
        logger.warning(f"error in cached data for repo {repo}: {data['error']}")
        return HTMLResponse(
            content=f"<p class='color-negative'>error: {data['error']}</p>",
            headers={"Widget-Title": "backups", "Widget-Content-Type": "html"},
        )

    # parse query parameters
    limit = int(request.query_params.get("limit", "1"))
    show_autorestic_icon = (
        request.query_params.get("autorestic-icon", "false").lower() == "true"
    )
    hide_file_count = (
        request.query_params.get("hide-file-count", "false").lower() == "true"
    )

    try:
        # format and render widget
        widget_data = format_backup_data(
            data,  # type: ignore - we checked for error above
            limit=limit,
            show_autorestic_icon=show_autorestic_icon,
            hide_file_count=hide_file_count,
        )
        html_content = render_widget(widget_data)

        return HTMLResponse(
            content=html_content,
            headers={"Widget-Title": "backups", "Widget-Content-Type": "html"},
        )
    except Exception as e:
        logger.error(f"failed to render widget for repo {repo}: {e}")
        return HTMLResponse(
            content=f"<p class='color-negative'>error rendering widget: {str(e)}</p>",
            status_code=500,
            headers={"Widget-Title": "backups", "Widget-Content-Type": "html"},
        )
