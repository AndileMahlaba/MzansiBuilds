from __future__ import annotations

from backend.extensions import db
from backend.models.user import User


class UserRepository:
    """Persistence for users. Lookup by email is O(1) average case with a hash index on email."""

    def get_by_id(self, user_id: int) -> User | None:
        return db.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        return db.session.query(User).filter_by(email=normalized).first()

    def create(self, name: str, email: str, password: str) -> User:
        user = User(name=name.strip(), email=email.strip().lower())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def update_profile(self, user: User, name: str | None, bio: str | None) -> User:
        if name is not None:
            user.name = name.strip()
        if bio is not None:
            user.bio = (bio or "")[:500]
        db.session.commit()
        return user
