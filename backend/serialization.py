from __future__ import annotations

from typing import Any

from backend.models.collaboration import CollaborationRequest
from backend.models.comment import Comment
from backend.models.milestone import Milestone
from backend.models.project import Project
from backend.models.user import User


def user_public(u: User) -> dict[str, Any]:
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "bio": (u.bio or "")[:500],
    }


def project_public(p: Project, include_owner: bool = True) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": p.id,
        "user_id": p.user_id,
        "title": p.title,
        "description": p.description or "",
        "stage": p.stage,
        "support_needed": p.support_needed or "",
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
    if include_owner and p.owner:
        out["owner"] = {"id": p.owner.id, "name": p.owner.name}
    return out


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
