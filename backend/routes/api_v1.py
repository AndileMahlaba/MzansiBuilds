from __future__ import annotations

from functools import wraps

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user

from backend.constants import PROJECT_STAGES
from backend.extensions import csrf
from backend.repositories.platform_repository import PlatformRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.user_repository import UserRepository
from backend.serialization import (
    collab_public,
    comment_public,
    milestone_public,
    project_public,
    user_public,
)
from backend.services.auth_service import AuthService
from backend.services.feed_service import FeedService
from backend.services.project_service import ProjectService

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
_auth = AuthService()
_repo = ProjectRepository()
_platform = PlatformRepository()
_svc = ProjectService()
_feed = FeedService()
_users = UserRepository()

API_VERSION = "1.0.0"


@api_v1_bp.route("", methods=["GET"])
def api_discovery():
    """Machine-readable catalog of the JSON API (similar to a public system index)."""
    return jsonify(
        system="MzansiBuilds — build in public",
        version=API_VERSION,
        theme="green · white · black",
        endpoints={
            "api_v1": "/api/v1",
            "health": "/api/v1/health",
            "ping": "/api/v1/ping",
            "stats": "/api/v1/stats",
            "auth_register": "/api/v1/auth/register",
            "auth_login": "/api/v1/auth/login",
            "auth_logout": "/api/v1/auth/logout",
            "me": "/api/v1/me",
            "me_projects": "/api/v1/me/projects",
            "feed": "/api/v1/feed",
            "feed_spotlight": "/api/v1/feed/spotlight",
            "celebration": "/api/v1/celebration",
            "projects": "/api/v1/projects",
            "project_by_id": "/api/v1/projects/<project_id>",
            "project_complete": "/api/v1/projects/<project_id>/complete",
            "project_comments": "/api/v1/projects/<project_id>/comments",
            "project_milestones": "/api/v1/projects/<project_id>/milestones",
            "project_collaboration": "/api/v1/projects/<project_id>/collaboration",
        },
    )


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify(error="Authentication required"), 401
        return view(*args, **kwargs)

    return wrapped


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@api_v1_bp.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", service="mzansibuilds")


@api_v1_bp.route("/ping", methods=["GET"])
def ping():
    return jsonify(ok=True, service="mzansibuilds")


@api_v1_bp.route("/stats", methods=["GET"])
def stats():
    """Platform-wide aggregates — same numbers power the /overview command center."""
    s = _platform.snapshot()
    return jsonify(
        developers=s.developers,
        active_projects=s.active_projects,
        completed_projects=s.completed_projects,
        milestones=s.milestones,
        comments=s.comments,
        pending_collaborations=s.pending_collaborations,
        stage_counts=s.stage_counts,
    )


@csrf.exempt
@api_v1_bp.route("/auth/register", methods=["POST"])
def register():
    body = _json_body()
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    if not name or not email or not password:
        return jsonify(error="name, email, and password are required"), 400
    user, err = _auth.register(name, email, password)
    if err:
        return jsonify(error=err), 400
    login_user(user)
    return jsonify(user=user_public(user)), 201


@csrf.exempt
@api_v1_bp.route("/auth/login", methods=["POST"])
def login():
    body = _json_body()
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    if not email or not password:
        return jsonify(error="email and password are required"), 400
    user = _auth.authenticate(email, password)
    if not user:
        return jsonify(error="Invalid email or password"), 401
    login_user(user)
    return jsonify(user=user_public(user))


@csrf.exempt
@api_v1_bp.route("/auth/logout", methods=["POST"])
@api_login_required
def logout():
    logout_user()
    return jsonify(ok=True)


@api_v1_bp.route("/me", methods=["GET"])
@api_login_required
def me():
    return jsonify(user=user_public(current_user))


@csrf.exempt
@api_v1_bp.route("/me", methods=["PATCH"])
@api_login_required
def patch_me():
    body = _json_body()
    name_kw = None
    if "name" in body:
        name_kw = str(body.get("name") or "").strip() or None
    bio_kw = None
    if "bio" in body:
        bio_kw = str(body.get("bio") or "")
    _users.update_profile(
        current_user,
        name_kw if "name" in body else None,
        bio_kw if "bio" in body else None,
    )
    return jsonify(user=user_public(current_user))


@api_v1_bp.route("/me/projects", methods=["GET"])
@api_login_required
def my_projects():
    summaries = _platform.owner_project_summaries(current_user.id)
    return jsonify(
        projects=[
            {
                "project": project_public(s.project),
                "milestone_count": s.milestone_count,
                "comment_count": s.comment_count,
            }
            for s in summaries
        ]
    )


@api_v1_bp.route("/feed", methods=["GET"])
def feed():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    try:
        per_page = min(50, max(1, int(request.args.get("per_page", 10))))
    except ValueError:
        per_page = 10
    stage = (request.args.get("stage") or "").strip().lower()
    if stage and stage not in PROJECT_STAGES:
        stage = ""
    result = _feed.page(page=page, per_page=per_page, stage=stage or None)
    items = [project_public(p) for p in result.items]
    return jsonify(
        projects=items,
        total=result.total,
        page=(result.offset // result.limit) + 1 if result.limit else 1,
        per_page=result.limit,
        has_next=result.has_next,
    )


@api_v1_bp.route("/feed/spotlight", methods=["GET"])
def feed_spotlight():
    try:
        k = min(10, max(1, int(request.args.get("k", 3))))
    except ValueError:
        k = 3
    try:
        pool = min(500, max(30, int(request.args.get("pool", 150))))
    except ValueError:
        pool = 150
    items = _feed.spotlight_newest(k=k, pool=pool)
    return jsonify(projects=[project_public(p) for p in items])


@api_v1_bp.route("/celebration", methods=["GET"])
def celebration():
    projects = _repo.list_celebration(limit=200)
    return jsonify(projects=[project_public(p) for p in projects])


@api_v1_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        return jsonify(error="Not found"), 404
    milestones = [milestone_public(m) for m in _repo.list_milestones_ordered(project_id)]
    comments = [comment_public(c) for c in _repo.list_comments(project_id)]
    collabs = [collab_public(r) for r in _repo.list_collaboration_for_project(project_id)]
    return jsonify(
        project=project_public(project),
        milestones=milestones,
        comments=comments,
        collaboration_requests=collabs,
    )


@csrf.exempt
@api_v1_bp.route("/projects", methods=["POST"])
@api_login_required
def create_project():
    body = _json_body()
    title = (body.get("title") or "").strip()
    description = (body.get("description") or "").strip()
    stage = (body.get("stage") or "").strip().lower()
    support = (body.get("support_needed") or "").strip()
    if not stage:
        return jsonify(error="stage is required"), 400
    if stage not in PROJECT_STAGES:
        return jsonify(error=f"stage must be one of: {', '.join(PROJECT_STAGES)}"), 400
    project, err = _svc.create(current_user, title, description, stage, support)
    if err:
        return jsonify(error=err), 400
    project = _repo.get_by_id(project.id)
    return jsonify(project=project_public(project)), 201


@csrf.exempt
@api_v1_bp.route("/projects/<int:project_id>", methods=["PATCH"])
@api_login_required
def patch_project(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        return jsonify(error="Not found"), 404
    body = _json_body()
    title = (body.get("title") or "").strip() if "title" in body else None
    description = body.get("description")
    if "description" in body and description is not None:
        description = str(description)
    elif "description" in body:
        description = ""
    else:
        description = None
    stage = None
    if "stage" in body and body.get("stage") is not None:
        stage = str(body.get("stage")).strip().lower()
    support_needed = None
    if "support_needed" in body:
        support_needed = (body.get("support_needed") or "").strip()
    _, err = _svc.update(
        project,
        current_user,
        title,
        description,
        stage,
        support_needed,
    )
    if err:
        return jsonify(error=err), 400
    project = _repo.get_by_id(project_id)
    return jsonify(project=project_public(project))


@csrf.exempt
@api_v1_bp.route("/projects/<int:project_id>/complete", methods=["POST"])
@api_login_required
def complete_project(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        return jsonify(error="Not found"), 404
    _, err = _svc.complete(project, current_user)
    if err:
        return jsonify(error=err), 400
    project = _repo.get_by_id(project_id)
    return jsonify(project=project_public(project))


@csrf.exempt
@api_v1_bp.route("/projects/<int:project_id>/comments", methods=["POST"])
@api_login_required
def post_comment(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        return jsonify(error="Not found"), 404
    body = _json_body()
    content = (body.get("content") or "").strip()
    _, err = _svc.add_comment(project, current_user, content)
    if err:
        return jsonify(error=err), 400
    comments = _repo.list_comments(project_id)
    last = comments[-1] if comments else None
    return jsonify(comment=comment_public(last) if last else None), 201


@csrf.exempt
@api_v1_bp.route("/projects/<int:project_id>/milestones", methods=["POST"])
@api_login_required
def post_milestone(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        return jsonify(error="Not found"), 404
    body = _json_body()
    title = (body.get("title") or "").strip()
    description = (body.get("description") or "").strip()
    _, err = _svc.add_milestone(project, current_user, title, description)
    if err:
        return jsonify(error=err), 400
    ms = _repo.list_milestones_ordered(project_id)
    last = ms[0] if ms else None
    return jsonify(milestone=milestone_public(last) if last else None), 201


@csrf.exempt
@api_v1_bp.route("/projects/<int:project_id>/collaboration", methods=["POST"])
@api_login_required
def post_collaboration(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        return jsonify(error="Not found"), 404
    body = _json_body()
    message = (body.get("message") or "").strip()
    _, err = _svc.request_collaboration(project, current_user, message)
    if err:
        return jsonify(error=err), 400
    rows = _repo.list_collaboration_for_project(project_id)
    last = rows[0] if rows else None
    return jsonify(collaboration_request=collab_public(last) if last else None), 201
