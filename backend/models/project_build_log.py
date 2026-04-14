from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from backend.extensions import db

if TYPE_CHECKING:
    from backend.models.project import Project
    from backend.models.user import User


class ProjectBuildLog(db.Model):
    """Timestamped work updates: what changed, ships, notes (public build journal)."""

    __tablename__ = "project_build_logs"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    project = db.relationship("Project", back_populates="build_logs")
    author = db.relationship("User", backref="build_logs")
