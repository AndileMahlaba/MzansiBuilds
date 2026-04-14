"""Signed, time-limited tokens (e.g. password reset links)."""

from __future__ import annotations

from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def _reset_serializer(secret_key: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key, salt="mzansi-password-reset-v1")


def make_password_reset_token(secret_key: str, user_id: int, email: str) -> str:
    return _reset_serializer(secret_key).dumps({"uid": int(user_id), "email": email})


def load_password_reset_token(secret_key: str, token: str, max_age: int = 3600) -> dict[str, Any] | None:
    try:
        data = _reset_serializer(secret_key).loads(token, max_age=max_age)
        if not isinstance(data, dict) or "uid" not in data:
            return None
        return data
    except (BadSignature, SignatureExpired):
        return None


def _verify_serializer(secret_key: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key, salt="mzansi-email-verify-v1")


def make_email_verify_token(secret_key: str, user_id: int, email: str) -> str:
    return _verify_serializer(secret_key).dumps({"uid": int(user_id), "email": email})


def load_email_verify_token(secret_key: str, token: str, max_age: int = 72 * 3600) -> dict[str, Any] | None:
    try:
        data = _verify_serializer(secret_key).loads(token, max_age=max_age)
        if not isinstance(data, dict) or "uid" not in data:
            return None
        return data
    except (BadSignature, SignatureExpired):
        return None
