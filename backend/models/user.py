from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from backend.extensions import db

if TYPE_CHECKING:
    from backend.models.project import Project


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(500), default="")
    profile_public = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    projects = db.relationship(
        "Project", back_populates="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    comments = db.relationship("Comment", back_populates="author", lazy="dynamic")

    def set_password(self, raw: str) -> None:
        # pbkdf2:sha256 avoids scrypt on some Windows/OpenSSL builds (malloc failures in CI/dev).
        self.password_hash = generate_password_hash(raw, method="pbkdf2:sha256")

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)
