from __future__ import annotations

import heapq
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.project import Project


def group_projects_by_stage(
    projects: list[Project],
    stage_order: tuple[str, ...],
) -> list[tuple[str, list[Project]]]:
    """
    Bucket projects by stage for the feed UI.

    Time O(n) for n projects on the page: one pass into buckets, then emit in preferred order.
    Space O(n) for the buckets plus output references.
    """
    buckets: defaultdict[str, list[Project]] = defaultdict(list)
    for p in projects:
        buckets[p.stage].append(p)

    ordered: list[tuple[str, list[Project]]] = []
    seen: set[str] = set()
    for stage in stage_order:
        if stage in buckets:
            ordered.append((stage, buckets[stage]))
            seen.add(stage)
    for stage, rows in buckets.items():
        if stage not in seen:
            ordered.append((stage, rows))
    return ordered


def newest_spotlight_projects(candidates: list[Project], k: int) -> list[Project]:
    """
    Pick the k most recently created projects using heapq.nlargest.

    Time O(m log k) for m candidates (better than sorting all m when k is small).
    Space O(k) for the heap machinery inside nlargest.
    """
    if k <= 0 or not candidates:
        return []
    k = min(k, len(candidates))
    return heapq.nlargest(k, candidates, key=lambda p: p.created_at)
