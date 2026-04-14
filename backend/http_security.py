"""HTTP security headers and application error handlers."""

from __future__ import annotations

from flask import Flask, render_template, request


def register_security_headers(app: Flask) -> None:
    """Set baseline headers on every response (defence in depth; not a substitute for safe code)."""

    @app.after_request
    def _security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), microphone=(), payment=()",
        )
        
        csp = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        return response


def register_error_handlers(app: Flask) -> None:
    from sqlalchemy.exc import OperationalError
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        if isinstance(exc, HTTPException):
            return exc
        if isinstance(exc, OperationalError):
            app.logger.warning("Database operational error: %s", exc)
            if app.config.get("TESTING"):
                raise
            return render_template("errors/503.html"), 503
        app.logger.exception("Unhandled error for %s %s", request.method, request.path)
        if app.config.get("TESTING"):
            raise
        return render_template("errors/500.html"), 500
