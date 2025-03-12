import subprocess
import json
import logging
from datetime import datetime, timezone
import humanize
from src.config import config

logger = logging.getLogger("restic-api")

# run a restic command with the given arguments
def run_restic(args, repo, password):
    try:
        result = subprocess.run(
            ["restic", "-r", repo] + args,
            capture_output=True, text=True,
            env={"RESTIC_PASSWORD": password}
        )

        if result.returncode != 0:
            logger.error(f"Restic error: {result.stderr}")
            return {"error": result.stderr.strip()}

        return json.loads(result.stdout) if result.stdout else {"error": "Empty response"}
    except Exception as e:
        return {"error": str(e)}

# get backup info for a given repository
def get_backup_info(repo, password):
    snapshots = run_restic(["snapshots", "--json"], repo, password)
    if "error" in snapshots:
        return snapshots

    stats = run_restic(["stats", "--json"], repo, password)
    if "error" in stats:
        return stats

    latest_snapshot = sorted(snapshots, key=lambda s: s["time"], reverse=True)[0] # sort snapshots by time to get the latest one
    dt = datetime.fromisoformat(latest_snapshot["time"].replace("Z", "+00:00")) # convert the time string to a datetime object
    human_time = humanize.naturaltime(datetime.now(timezone.utc) - dt) # get the human readable time

    return {
        "latest_snapshot": {
            "time": human_time,
            "id": latest_snapshot.get("short_id", ""),
            "tags": latest_snapshot.get("tags", [])
        },
        "stats": {
            "total_size": humanize.naturalsize(stats.get("total_size", 0)),
            "file_count": stats.get("total_file_count", 0),
            "snapshots_count": stats.get("snapshots_count", 0)
        }
    }