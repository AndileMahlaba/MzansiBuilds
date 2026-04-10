from __future__ import annotations

from dataclasses import dataclass

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

    Rough complexity: O(k) for k items on the page from the DB planner's perspective, with an
    index on created_at giving O(log n) seek into the active set for n total projects.
    """

    def __init__(self, projects: ProjectRepository | None = None) -> None:
        self._projects = projects or ProjectRepository()

    def page(self, page: int, per_page: int) -> FeedPage:
        page = max(1, page)
        per_page = min(50, max(1, per_page))
        offset = (page - 1) * per_page
        total = self._projects.count_active()
        items = self._projects.list_feed_page(offset=offset, limit=per_page)
        return FeedPage(items=items, total=total, offset=offset, limit=per_page)
