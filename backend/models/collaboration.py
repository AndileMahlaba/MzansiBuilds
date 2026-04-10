from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from backend.extensions import db

if TYPE_CHECKING:
    from backend.models.project import Project
    from backend.models.user import User


class CollaborationRequest(db.Model):
    __tablename__ = "collaboration_requests"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(500), default="")
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    project = db.relationship("Project", back_populates="collaboration_requests")
    requester = db.relationship("User")
