from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from backend.extensions import db

if TYPE_CHECKING:
    from backend.models.project import Project
    from backend.models.user import User


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    project = db.relationship("Project", back_populates="comments")
    author = db.relationship("User", back_populates="comments")
