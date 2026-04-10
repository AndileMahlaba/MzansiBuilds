from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from backend.extensions import db

if TYPE_CHECKING:
    from backend.models.project import Project


class Milestone(db.Model):
    __tablename__ = "milestones"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    achieved_at = db.Column(db.Date, default=lambda: date.today(), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    project = db.relationship("Project", back_populates="milestones")
