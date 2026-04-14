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

    def create(
        self, name: str, email: str, password: str, *, email_verified: bool = True
    ) -> User:
        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            email_verified=email_verified,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def mark_email_verified(self, user: User) -> User:
        user.email_verified = True
        db.session.commit()
        return user

    def update_profile(
        self,
        user: User,
        name: str | None,
        bio: str | None,
        profile_public: bool | None = None,
    ) -> User:
        if name is not None:
            user.name = name.strip()
        if bio is not None:
            user.bio = (bio or "")[:500]
        if profile_public is not None:
            user.profile_public = bool(profile_public)
        db.session.commit()
        return user

    def change_password(self, user: User, old_password: str, new_password: str) -> str | None:
        if not user.check_password(old_password):
            return "Current password is incorrect."
        if len(new_password) < 8:
            return "New password should be at least 8 characters."
        user.set_password(new_password)
        db.session.commit()
        return None

    def apply_new_password(self, user: User, new_password: str) -> None:
        if len(new_password) < 8:
            raise ValueError("Password should be at least 8 characters.")
        user.set_password(new_password)
        db.session.commit()
