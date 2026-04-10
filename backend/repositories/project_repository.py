from __future__ import annotations

from sqlalchemy.orm import joinedload

from backend.constants import PROJECT_ACTIVE
from backend.extensions import db
from backend.models.collaboration import CollaborationRequest
from backend.models.comment import Comment
from backend.models.milestone import Milestone
from backend.models.project import Project
from backend.models.user import User


class ProjectRepository:
    """Project and related entity access. Feed queries use eager loading to avoid N+1 selects."""

    def get_by_id(self, project_id: int) -> Project | None:
        return (
            db.session.query(Project)
            .options(joinedload(Project.owner))
            .filter_by(id=project_id)
            .first()
        )

    def list_feed_page(self, offset: int, limit: int) -> list[Project]:
        """Active projects newest first. Indexed created_at keeps this O(log n + k) for k rows returned."""
        return (
            db.session.query(Project)
            .options(joinedload(Project.owner))
            .filter(Project.status == PROJECT_ACTIVE)
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_active(self) -> int:
        return db.session.query(Project).filter(Project.status == PROJECT_ACTIVE).count()

    def list_celebration(self, limit: int = 100) -> list[Project]:
        from backend.constants import PROJECT_COMPLETED

        return (
            db.session.query(Project)
            .options(joinedload(Project.owner))
            .filter(Project.status == PROJECT_COMPLETED)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .all()
        )

    def create(
        self,
        owner: User,
        title: str,
        description: str,
        stage: str,
        support_needed: str,
    ) -> Project:
        p = Project(
            user_id=owner.id,
            title=title.strip(),
            description=(description or "").strip(),
            stage=stage.strip().lower(),
            support_needed=(support_needed or "").strip()[:200],
            status=PROJECT_ACTIVE,
        )
        db.session.add(p)
        db.session.commit()
        return p

    def update(
        self,
        project: Project,
        title: str | None,
        description: str | None,
        stage: str | None,
        support_needed: str | None,
    ) -> Project:
        if title is not None:
            project.title = title.strip()[:200]
        if description is not None:
            project.description = (description or "")[:20000]
        if stage is not None:
            project.stage = stage.strip().lower()[:40]
        if support_needed is not None:
            project.support_needed = (support_needed or "")[:200]
        db.session.commit()
        return project

    def mark_completed(self, project: Project) -> Project:
        from backend.constants import PROJECT_COMPLETED

        project.status = PROJECT_COMPLETED
        db.session.commit()
        return project

    def list_milestones_ordered(self, project_id: int) -> list[Milestone]:
        return (
            db.session.query(Milestone)
            .filter_by(project_id=project_id)
            .order_by(Milestone.achieved_at.desc(), Milestone.id.desc())
            .all()
        )

    def add_milestone(
        self, project_id: int, title: str, description: str
    ) -> Milestone:
        m = Milestone(
            project_id=project_id,
            title=title.strip()[:200],
            description=(description or "")[:5000],
        )
        db.session.add(m)
        db.session.commit()
        return m

    def add_comment(self, project_id: int, user_id: int, content: str) -> Comment:
        c = Comment(
            project_id=project_id,
            user_id=user_id,
            content=content.strip()[:5000],
        )
        db.session.add(c)
        db.session.commit()
        return c

    def list_comments(self, project_id: int) -> list[Comment]:
        return (
            db.session.query(Comment)
            .options(joinedload(Comment.author))
            .filter_by(project_id=project_id)
            .order_by(Comment.created_at.asc())
            .all()
        )

    def add_collaboration_request(
        self, project_id: int, requester_id: int, message: str
    ) -> CollaborationRequest:
        r = CollaborationRequest(
            project_id=project_id,
            requester_id=requester_id,
            message=(message or "").strip()[:500],
        )
        db.session.add(r)
        db.session.commit()
        return r

    def list_collaboration_for_project(
        self, project_id: int
    ) -> list[CollaborationRequest]:
        return (
            db.session.query(CollaborationRequest)
            .options(joinedload(CollaborationRequest.requester))
            .filter_by(project_id=project_id)
            .order_by(CollaborationRequest.created_at.desc())
            .all()
        )
