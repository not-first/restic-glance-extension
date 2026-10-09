import json
import logging
import os
import subprocess
import time
from typing import Any

from src.config import config as global_config
from src.types import BackupInfo, RepoConfig, SnapshotData, StatsData

logger = logging.getLogger("restic-api")


class ResticError(Exception):
    # raised when restic command fails

    pass


# wrapper for restic repository operations
class ResticRepo:
    def __init__(self, config: RepoConfig) -> None:
        self.password = config["password"]
        self.env = {
            "RESTIC_PASSWORD": config["password"],
        } | config["env"]
        self.url = config["url"]

    # run a restic command with the given arguments
    def run_restic(self, *args: str) -> dict[str, Any]:
        started = time.monotonic()
        command_kind = args[0] if args else "unknown"
        try:
            restic_command = ["restic", "-r", self.url] + list(args)

            env = os.environ.copy()
            env.update(self.env)

            result = subprocess.run(
                restic_command,
                capture_output=True,
                text=True,
                env=env,
                timeout=global_config.COMMAND_TIMEOUT,
            )

            logger.info(
                "restic %s finished in %.1fs (deadline=%ss, exit=%s)",
                command_kind,
                time.monotonic() - started,
                global_config.COMMAND_TIMEOUT,
                result.returncode,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                logger.error(f"restic command failed: {error_msg}")
                return {"error": error_msg}

            if not result.stdout:
                logger.warning("restic command returned empty output")
                return {"error": "empty response from restic"}

            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(f"failed to parse restic json output: {e}")
                return {"error": f"invalid json response: {str(e)}"}

        except subprocess.TimeoutExpired:
            logger.error(
                "restic %s timed out after %.1fs (deadline=%ss)",
                command_kind,
                time.monotonic() - started,
                global_config.COMMAND_TIMEOUT,
            )
            return {"error": "restic command timed out"}
        except Exception as e:
            logger.error(f"unexpected error running restic: {e}")
            return {"error": str(e)}

    # get backup info for a given repository
    def get_backup_info(
        self, stats_mode: str = "repository-size"
    ) -> BackupInfo | dict[str, str]:
        snapshots = self.run_restic("snapshots", "--json")
        if "error" in snapshots:
            logger.warning(f"failed to fetch snapshots: {snapshots['error']}")
            return snapshots

        if not isinstance(snapshots, list):
            logger.error(f"unexpected snapshots response type: {type(snapshots)}")
            return {"error": "invalid snapshots response format"}

        if not snapshots:
            logger.warning("no snapshots found in repository")
            return {"error": "no snapshots available"}

        # map stats mode to restic command
        if stats_mode == "repository-size":
            # show actual disk usage of the repository
            stats = self.run_restic("stats", "--json", "--mode", "raw-data")
        elif stats_mode == "latest-snapshot":
            # show restore size of the latest snapshot only
            stats = self.run_restic(
                "stats", "latest", "--json", "--mode", "restore-size"
            )
        else:
            logger.error(f"invalid stats mode: {stats_mode}")
            return {"error": f"invalid stats mode: {stats_mode}"}

        if "error" in stats:
            logger.warning(f"failed to fetch stats: {stats['error']}")
            return stats

        sorted_snaps: list[SnapshotData] = sorted(
            snapshots, key=lambda s: s["time"], reverse=True
        )

        stats_data: StatsData = {
            "total_size": stats.get("total_size", 0),
            "file_count": stats.get("total_file_count", 0),
            "snapshots_count": len(sorted_snaps),
        }

        backup_info: BackupInfo = {
            "all_snapshots": sorted_snaps,
            "latest_snapshot": {
                "time": sorted_snaps[0]["time"],
                "id": sorted_snaps[0].get("short_id", ""),
                "short_id": sorted_snaps[0].get("short_id", ""),
                "tags": sorted_snaps[0].get("tags", []),
            },
            "stats": stats_data,
        }

        return backup_info
