from datetime import datetime, timezone

from backend.algorithms.feed_layout import group_projects_by_stage, newest_spotlight_projects


class _P:
    def __init__(self, pid: int, stage: str, created_at: datetime) -> None:
        self.id = pid
        self.stage = stage
        self.created_at = created_at


def test_group_projects_by_stage_orders_buckets():
    order = ("idea", "testing", "development")
    projects = [
        _P(1, "development", datetime.now(timezone.utc)),
        _P(2, "idea", datetime.now(timezone.utc)),
        _P(3, "testing", datetime.now(timezone.utc)),
    ]
    grouped = group_projects_by_stage(projects, order)
    labels = [g[0] for g in grouped]
    assert labels == ["idea", "testing", "development"]


def test_newest_spotlight_projects_heap():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2026, 3, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 2, 1, tzinfo=timezone.utc)
    rows = [_P(1, "idea", t0), _P(2, "idea", t1), _P(3, "idea", t2)]
    top = newest_spotlight_projects(rows, 2)
    assert [p.id for p in top] == [2, 3]
