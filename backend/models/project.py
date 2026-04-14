from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from backend.extensions import db

if TYPE_CHECKING:
    from backend.models.user import User


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    repo_url = db.Column(db.String(500), default="")
    demo_url = db.Column(db.String(500), default="")
    stage = db.Column(db.String(40), nullable=False, index=True)
    support_needed = db.Column(db.String(200), default="")
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    owner = db.relationship("User", back_populates="projects")
    milestones = db.relationship(
        "Milestone",
        back_populates="project",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    comments = db.relationship(
        "Comment", back_populates="project", lazy="dynamic", cascade="all, delete-orphan"
    )
    collaboration_requests = db.relationship(
        "CollaborationRequest",
        back_populates="project",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    build_logs = db.relationship(
        "ProjectBuildLog",
        back_populates="project",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
