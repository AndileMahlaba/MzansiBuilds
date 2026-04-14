from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func

from backend.constants import COLLAB_PENDING, PROJECT_ACTIVE, PROJECT_COMPLETED, PROJECT_STAGES
from backend.extensions import db
from backend.models.collaboration import CollaborationRequest
from backend.models.comment import Comment
from backend.models.milestone import Milestone
from backend.models.project import Project
from backend.models.user import User
from sqlalchemy.orm import joinedload


@dataclass(frozen=True)
class PlatformSnapshot:
    """Aggregate metrics across the whole platform (O(1) queries per counter, grouped stage scan)."""

    developers: int
    active_projects: int
    completed_projects: int
    milestones: int
    comments: int
    pending_collaborations: int
    stage_counts: dict[str, int]


@dataclass(frozen=True)
class OwnerProjectSummary:
    project: Project
    milestone_count: int
    comment_count: int


class PlatformRepository:
    """
    Read-only aggregates for dashboards and `/api/v1/stats`.

    Complexity notes for `snapshot()` are documented in `docs/ALGORITHMS_AND_COMPLEXITY.md`
    (scalar counts + one grouped aggregation over active projects).
    """

    def snapshot(self) -> PlatformSnapshot:
        developers = int(db.session.query(func.count(User.id)).scalar() or 0)
        active_projects = int(
            db.session.query(func.count(Project.id))
            .filter(Project.status == PROJECT_ACTIVE)
            .scalar()
            or 0
        )
        completed_projects = int(
            db.session.query(func.count(Project.id))
            .filter(Project.status == PROJECT_COMPLETED)
            .scalar()
            or 0
        )
        milestones = int(db.session.query(func.count(Milestone.id)).scalar() or 0)
        comments = int(db.session.query(func.count(Comment.id)).scalar() or 0)
        pending_collaborations = int(
            db.session.query(func.count(CollaborationRequest.id))
            .filter(CollaborationRequest.status == COLLAB_PENDING)
            .scalar()
            or 0
        )

        rows = (
            db.session.query(Project.stage, func.count(Project.id))
            .filter(Project.status == PROJECT_ACTIVE)
            .group_by(Project.stage)
            .all()
        )
        raw = {str(stage): int(n) for stage, n in rows}
        stage_counts = {s: int(raw.get(s, 0)) for s in PROJECT_STAGES}

        return PlatformSnapshot(
            developers=developers,
            active_projects=active_projects,
            completed_projects=completed_projects,
            milestones=milestones,
            comments=comments,
            pending_collaborations=pending_collaborations,
            stage_counts=stage_counts,
        )

    def recent_comments(self, limit: int = 8) -> list[Comment]:
        return (
            db.session.query(Comment)
            .options(
                joinedload(Comment.author),
                joinedload(Comment.project),
            )
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .all()
        )

    def owner_project_summaries(
        self, user_id: int, limit: int = 12
    ) -> list[OwnerProjectSummary]:
        projects = (
            db.session.query(Project)
            .options(joinedload(Project.owner))
            .filter(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .all()
        )
        if not projects:
            return []
        ids = [p.id for p in projects]
        mc = self._counts_per_project(Milestone, ids)
        cc = self._counts_per_project(Comment, ids)
        return [
            OwnerProjectSummary(
                project=p,
                milestone_count=mc.get(p.id, 0),
                comment_count=cc.get(p.id, 0),
            )
            for p in projects
        ]

    def _counts_per_project(self, model, project_ids: list[int]) -> dict[int, int]:
        if not project_ids:
            return {}
        rows = (
            db.session.query(model.project_id, func.count(model.id))
            .filter(model.project_id.in_(project_ids))
            .group_by(model.project_id)
            .all()
        )
        return {int(pid): int(n) for pid, n in rows}
