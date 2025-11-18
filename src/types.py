from typing import TypedDict, NotRequired


# snapshot data from restic
class SnapshotData(TypedDict):
    time: str
    short_id: str
    id: str
    tags: NotRequired[list[str]]


# repository statistics from restic
class StatsData(TypedDict):
    total_size: int
    total_file_count: int
    snapshots_count: int


# restic stats command response
class ResticStats(TypedDict):
    total_size: int
    total_file_count: int
    snapshots_count: int


# complete backup information for a repository
class BackupInfo(TypedDict):
    all_snapshots: list[SnapshotData]
    latest_snapshot: SnapshotData
    stats: StatsData


# formatted snapshot data for display
class FormattedSnapshot(TypedDict):
    id: str
    readable_time: str
    method: NotRequired[str]


# formatted statistics for display
class FormattedStats(TypedDict):
    total_size: str
    file_count: str
    snapshots_count: int


# complete widget display data
class WidgetData(TypedDict):
    snapshot_id: str
    snapshot_time: str
    snapshots_count: int
    total_file_count: str
    total_size: str
    hide_file_count: bool
    method: NotRequired[str]
    other_snapshots: list[FormattedSnapshot]


# configuration for a single restic repository
class RepoConfig(TypedDict):
    password: str
    url: str
    env: dict[str, str]
