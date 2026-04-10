from datetime import date

from backend.algorithms.milestone_timeline import merge_sorted_milestones


def test_merge_sorted_milestones_interleaves_newest_first():
    left = [
        (date(2026, 4, 2), 2, "API"),
        (date(2026, 4, 1), 1, "Scaffold"),
    ]
    right = [
        (date(2026, 4, 3), 3, "Deploy"),
        (date(2026, 3, 30), 0, "Ideas"),
    ]
    got = merge_sorted_milestones(left, right)
    titles = [g[2] for g in got]
    assert titles == ["Deploy", "API", "Scaffold", "Ideas"]
