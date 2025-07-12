import subprocess
import json
import logging
import humanize
import os

logger = logging.getLogger("restic-api")
class ResticRepo:
    def __init__(self, config):
        self.password = config["password"]
        self.env = {
            "RESTIC_PASSWORD": config["password"],
        } | config["env"]

        self.url =  config["url"]

    # run a restic command with the given arguments
    def run_restic(self, *args):
        try:
            restic_command = ["restic", "-r", self.url] + [*args]
            logger.debug(f"Running restic command: {restic_command}")
            env = os.environ.copy()
            env.update(self.env)
            result = subprocess.run(
                restic_command,
                capture_output=True,
                text=True,
                env=env
            )

            if result.returncode != 0:
                logger.error(f"Restic error: {result.stderr}")
                return {"error": result.stderr.strip()}

            return (
                json.loads(result.stdout) if result.stdout else {"error": "Empty response"}
            )
        except Exception as e:
            return {"error": str(e)}


    # get backup info for a given repository
    def get_backup_info(self):
        snapshots = self.run_restic("snapshots", "--json")
        if "error" in snapshots:
            return snapshots

        # use the mode from the environment variable
        mode = self.env.get("RESTIC_REPOS_MODE", "restore-size")
        stats = self.run_restic("stats", "--json", "--mode", mode)
        if "error" in stats:
            return stats

        sorted_snaps = sorted(snapshots, key=lambda s: s["time"], reverse=True)

        return {
            "all_snapshots": sorted_snaps,
            "latest_snapshot": {
                "time": sorted_snaps[0]["time"],
                "id": sorted_snaps[0].get("short_id", ""),
                "tags": sorted_snaps[0].get("tags", []),
            },
            "stats": {
                "total_size": humanize.naturalsize(stats.get("total_size", 0)),
                "file_count": humanize.intcomma(stats.get("total_file_count", 0)),
                "snapshots_count": stats.get("snapshots_count", 0),
            },
        }
