from __future__ import annotations

from typing import Any

from backend.models.collaboration import CollaborationRequest
from backend.models.comment import Comment
from backend.models.milestone import Milestone
from backend.models.project import Project
from backend.models.project_build_log import ProjectBuildLog
from backend.models.user import User


def user_public(u: User, *, viewer_id: int | None = None, include_email: bool | None = None) -> dict[str, Any]:
    """Serialize a user. Email is only included for the account owner unless include_email is True."""
    same = viewer_id is not None and viewer_id == u.id
    if include_email is None:
        include_email = same
    show_bio = bool(getattr(u, "profile_public", True)) or same
    out: dict[str, Any] = {
        "id": u.id,
        "name": u.name,
        "bio": ((u.bio or "")[:500] if show_bio else ""),
        "profile_public": bool(getattr(u, "profile_public", True)),
        "email_verified": bool(getattr(u, "email_verified", True)),
    }
    if include_email:
        out["email"] = u.email
    return out


def project_public(
    p: Project,
    include_owner: bool = True,
    *,
    viewer_id: int | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": p.id,
        "user_id": p.user_id,
        "title": p.title,
        "description": p.description or "",
        "repo_url": getattr(p, "repo_url", None) or "",
        "demo_url": getattr(p, "demo_url", None) or "",
        "stage": p.stage,
        "support_needed": p.support_needed or "",
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
    if include_owner and p.owner:
        out["owner"] = user_public(p.owner, viewer_id=viewer_id)
    return out


def build_log_public(log: ProjectBuildLog) -> dict[str, Any]:
    return {
        "id": log.id,
        "project_id": log.project_id,
        "user_id": log.user_id,
        "title": log.title,
        "body": log.body or "",
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "author_name": log.author.name if log.author else None,
    }


def milestone_public(m: Milestone) -> dict[str, Any]:
    return {
        "id": m.id,
        "project_id": m.project_id,
        "title": m.title,
        "description": m.description or "",
        "achieved_at": m.achieved_at.isoformat() if m.achieved_at else None,
    }


def comment_public(c: Comment) -> dict[str, Any]:
    return {
        "id": c.id,
        "project_id": c.project_id,
        "user_id": c.user_id,
        "content": c.content,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "author_name": c.author.name if c.author else None,
    }


def collab_public(r: CollaborationRequest) -> dict[str, Any]:
    return {
        "id": r.id,
        "project_id": r.project_id,
        "requester_id": r.requester_id,
        "message": r.message or "",
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "requester_name": r.requester.name if r.requester else None,
    }
