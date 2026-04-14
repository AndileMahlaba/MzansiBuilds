from __future__ import annotations

from backend.models.user import User
from backend.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, users: UserRepository | None = None) -> None:
        self._users = users or UserRepository()

    def register(
        self,
        name: str,
        email: str,
        password: str,
        *,
        email_verified: bool = True,
    ) -> tuple[User | None, str | None]:
        if self._users.get_by_email(email):
            return None, "An account with that email already exists."
        if len(password) < 8:
            return None, "Password should be at least 8 characters."
        user = self._users.create(name, email, password, email_verified=email_verified)
        return user, None

    def authenticate(self, email: str, password: str) -> User | None:
        user = self._users.get_by_email(email)
        if not user or not user.check_password(password):
            return None
        return user
