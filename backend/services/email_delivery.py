from __future__ import annotations

from flask import current_app, url_for

from backend.models.user import User
from backend.utils.smtp_mail import mail_is_configured, send_plain_text_email
from backend.utils.tokens import make_email_verify_token, make_password_reset_token


def build_verification_url(user: User) -> str:
    token = make_email_verify_token(current_app.config["SECRET_KEY"], user.id, user.email)
    return url_for("main.verify_email", token=token, _external=True)


def build_password_reset_url(user: User) -> str:
    token = make_password_reset_token(current_app.config["SECRET_KEY"], user.id, user.email)
    return url_for("main.reset_password", token=token, _external=True)


def send_verification_email(user: User) -> tuple[bool, str | None]:
    app = current_app._get_current_object()
    verify_url = build_verification_url(user)
    body = (
        f"Hi {user.name},\n\n"
        f"Welcome to MzansiBuilds. Confirm your email to activate your account:\n\n"
        f"{verify_url}\n\n"
        f"If you did not create an account, you can ignore this message.\n"
    )
    ok, err = send_plain_text_email(
        app,
        user.email,
        "Confirm your MzansiBuilds email",
        body,
    )
    if ok:
        app.logger.info("Verification email sent to %s", user.email)
    elif mail_is_configured(app):
        app.logger.error("Failed to send verification email: %s", err)
    return ok, err


def send_password_reset_email(user: User) -> tuple[bool, str | None]:
    app = current_app._get_current_object()
    reset_url = build_password_reset_url(user)
    body = (
        f"Hi {user.name},\n\n"
        f"Reset your MzansiBuilds password using this link (valid for a limited time):\n\n"
        f"{reset_url}\n\n"
        f"If you did not request a reset, you can ignore this message.\n"
    )
    ok, err = send_plain_text_email(
        app,
        user.email,
        "Reset your MzansiBuilds password",
        body,
    )
    if ok:
        app.logger.info("Password reset email sent to %s", user.email)
    elif mail_is_configured(app):
        app.logger.error("Failed to send password reset email: %s", err)
    return ok, err
