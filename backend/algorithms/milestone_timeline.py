from __future__ import annotations

from collections.abc import Sequence
from datetime import date


def merge_sorted_milestones(
    left: Sequence[tuple[date, int, str]],
    right: Sequence[tuple[date, int, str]],
) -> list[tuple[date, int, str]]:
    """
    Merge two sequences that are each sorted by (achieved_at desc, id desc).

    Time: O(n + m) where n = len(left), m = len(right).
    Space: O(n + m) for the output list.

    I used this pattern so I could reason about combining cached slices without resorting to
    resorting the full list when the inputs are already ordered (same idea as merge step in
    merge-sort, but applied to two known-sorted runs).
    """
    i, j = 0, 0
    out: list[tuple[date, int, str]] = []

    def better(a: tuple[date, int, str], b: tuple[date, int, str]) -> bool:
        if a[0] != b[0]:
            return a[0] > b[0]
        return a[1] > b[1]

    while i < len(left) and j < len(right):
        if better(left[i], right[j]):
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    while i < len(left):
        out.append(left[i])
        i += 1
    while j < len(right):
        out.append(right[j])
        j += 1
    return out
