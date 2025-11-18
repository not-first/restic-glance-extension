import logging
from datetime import datetime, timezone

import humanize
from dateutil.parser import isoparse

from src.types import BackupInfo, FormattedSnapshot, WidgetData

logger = logging.getLogger("restic-api")


# transform raw backup info into formatted widget data
def format_backup_data(
    backup_info: BackupInfo,
    limit: int = 1,
    show_autorestic_icon: bool = False,
    hide_file_count: bool = False,
) -> WidgetData:
    all_snaps = backup_info["all_snapshots"][:limit]
    stats = backup_info["stats"]

    # format snapshots with readable time
    formatted_snaps: list[FormattedSnapshot] = []
    for snap in all_snaps:
        dt = isoparse(snap["time"])
        readable_time = humanize.naturaltime(datetime.now(timezone.utc) - dt)

        formatted_snap: FormattedSnapshot = {
            "id": snap.get("short_id", ""),
            "readable_time": readable_time,
        }

        # add backup method if autorestic icon enabled
        if show_autorestic_icon:
            tags = snap.get("tags", [])
            formatted_snap["method"] = "cron" if "ar:cron" in tags else "manual"

        formatted_snaps.append(formatted_snap)

    # prepare widget data
    latest = formatted_snaps[0] if formatted_snaps else None
    if not latest:
        raise ValueError("no snapshots available to format")

    widget_data: WidgetData = {
        "snapshot_id": latest["id"],
        "snapshot_time": latest["readable_time"],
        "snapshots_count": stats["snapshots_count"],
        "total_file_count": humanize.intcomma(stats["file_count"]),
        "total_size": humanize.naturalsize(stats["total_size"]),
        "hide_file_count": hide_file_count,
        "other_snapshots": formatted_snaps[1:] if len(formatted_snaps) > 1 else [],
    }

    # add method to widget data if present
    if "method" in latest:
        widget_data["method"] = latest["method"]

    logger.debug(f"formatted {len(formatted_snaps)} snapshots for display")

    return widget_data
