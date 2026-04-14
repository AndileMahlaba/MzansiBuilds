"""Minimal SMTP send (stdlib). Used when MAIL_SERVER is set."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def mail_is_configured(app: Flask) -> bool:
    c = app.config
    return bool(c.get("MAIL_SERVER") and c.get("MAIL_USERNAME"))


def send_plain_text_email(
    app: Flask,
    to_addr: str,
    subject: str,
    body: str,
) -> tuple[bool, str | None]:
    """Return (ok, error_message)."""
    if not mail_is_configured(app):
        return False, "Mail is not configured (set MAIL_SERVER and MAIL_USERNAME)."
    c = app.config
    sender = c.get("MAIL_DEFAULT_SENDER") or c.get("MAIL_USERNAME")
    if not sender:
        return False, "MAIL_DEFAULT_SENDER or MAIL_USERNAME required."
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content(body)
    host = c["MAIL_SERVER"]
    port = int(c.get("MAIL_PORT") or 587)
    use_tls = bool(c.get("MAIL_USE_TLS"))
    use_ssl = bool(c.get("MAIL_USE_SSL")) or port == 465
    user = c.get("MAIL_USERNAME")
    password = c.get("MAIL_PASSWORD") or ""
    try:
        if use_ssl and port == 465:
            # Gmail / many hosts: SSL on 465
            with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
        elif use_tls:
            # STARTTLS on 587 (common)
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.starttls()
                smtp.login(user, password)
                smtp.send_message(msg)
        else:
            # Plain SMTP (rare); try without TLS
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        return False, f"SMTP auth failed (check username/app password): {e}"
    except OSError as e:
        return False, str(e)
