from __future__ import annotations

from dataclasses import dataclass

from backend.algorithms.feed_layout import newest_spotlight_projects
from backend.models.project import Project
from backend.repositories.project_repository import ProjectRepository


@dataclass(frozen=True)
class FeedPage:
    """One page of feed results plus total count for pagination UI."""

    items: list[Project]
    total: int
    offset: int
    limit: int

    @property
    def has_next(self) -> bool:
        return self.offset + len(self.items) < self.total


class FeedService:
    """
    Builds the developer feed. Pagination is index-friendly: we only fetch `limit` rows per page.

    Spotlight selection delegates to `backend.algorithms.feed_layout.newest_spotlight_projects`
    (heap-based top-k). See `docs/ALGORITHMS_AND_COMPLEXITY.md` for Big-O notes.

    DB planner: typically O(k) rows returned with an index seek on `created_at` for the active set.
    """

    def __init__(self, projects: ProjectRepository | None = None) -> None:
        self._projects = projects or ProjectRepository()

    def page(
        self, page: int, per_page: int, stage: str | None = None
    ) -> FeedPage:
        page = max(1, page)
        per_page = min(50, max(1, per_page))
        offset = (page - 1) * per_page
        total = self._projects.count_active(stage=stage)
        items = self._projects.list_feed_page(
            offset=offset, limit=per_page, stage=stage
        )
        return FeedPage(items=items, total=total, offset=offset, limit=per_page)

    def spotlight_newest(self, k: int = 3, pool: int = 150) -> list[Project]:
        """Global freshest builds for the hero row; selection uses a heap on the candidate pool."""
        pool_rows = self._projects.list_active_pool_unordered(pool)
        return newest_spotlight_projects(pool_rows, k)
