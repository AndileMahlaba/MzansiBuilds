from __future__ import annotations

"""Browser routes: server-rendered HTML (Jinja) and static assets for SSR CSS."""

from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.orm import joinedload

from backend.constants import (
    PROJECT_ACTIVE,
    PROJECT_COMPLETED,
    PROJECT_STAGES,
)
from backend.extensions import db
from backend.models.project import Project
from backend.repositories.platform_repository import PlatformRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.user_repository import UserRepository
from backend.routes.api_v1 import API_VERSION
from backend.services.auth_service import AuthService
from backend.services.feed_service import FeedService
from backend.services.project_service import ProjectService

main_bp = Blueprint("main", __name__)

_BACKEND_PKG = Path(__file__).resolve().parent.parent

_auth = AuthService()
_platform = PlatformRepository()
_projects = ProjectRepository()
_users = UserRepository()
_svc = ProjectService()


@main_bp.route("/__mzansi-ui-check")
def mzansi_ui_check():
    """JSON probe: confirms SSR assets and templates are available (no React build required)."""
    css = _BACKEND_PKG / "static" / "css" / "mzansi_ssr.css"
    tpl = Path(current_app.root_path) / "templates" / "base.html"
    ok = css.is_file() and tpl.is_file()
    return jsonify(
        ok=ok,
        mode="ssr",
        theme_css=url_for("main.mzansi_assets", subpath="css/mzansi_ssr.css"),
        static_url=url_for("static", filename="css/mzansi_ssr.css"),
        css_exists=css.is_file(),
        base_template_exists=tpl.is_file(),
        feed_url=url_for("main.ssr_feed", _external=False),
        hint="Primary theme URL is /mzansi-assets/css/mzansi_ssr.css. JSON API: /api/v1.",
    )


@main_bp.route("/mzansi-assets/<path:subpath>")
def mzansi_assets(subpath: str):
    """Serve files from ``backend/static`` on a URL the ``/<path:path>`` catch-all cannot shadow."""
    return send_from_directory(_BACKEND_PKG / "static", subpath, max_age=86400)


ALLOWED_PROJECT_STATUS = frozenset({PROJECT_ACTIVE, PROJECT_COMPLETED})


@main_bp.route("/")
def home():
    """Marketing landing (same era as the old React home)."""
    return render_template(
        "landing.html",
        nav_active="overview",
        api_version=API_VERSION,
    )


@main_bp.route("/overview")
def overview_redirect():
    return redirect(url_for("main.home"), code=302)


@main_bp.route("/feed")
def feed_redirect():
    return redirect(url_for("main.ssr_feed"), code=302)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    summaries = _platform.owner_project_summaries(current_user.id)
    snapshot = _platform.snapshot()
    return render_template(
        "dashboard_ssr.html",
        summaries=summaries,
        snapshot=snapshot,
        sidebar_active="dashboard",
    )


@main_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        bio = (request.form.get("bio") or "")[:500]
        if name:
            _users.update_profile(current_user, name, bio)
            flash("Profile updated.", "success")
        return redirect(url_for("main.account"))
    return render_template("account_ssr.html", sidebar_active="account")


@main_bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        stage = (request.form.get("stage") or "").strip().lower()
        support = (request.form.get("support_needed") or "").strip()
        proj, err = _svc.create(current_user, title, description, stage, support)
        if err:
            return render_template(
                "project_form.html",
                project=None,
                stages=PROJECT_STAGES,
                sidebar_active="new",
                error=err,
            )
        flash("Project created.", "success")
        return redirect(url_for("main.project_detail", project_id=proj.id))
    return render_template(
        "project_form.html",
        project=None,
        stages=PROJECT_STAGES,
        sidebar_active="new",
    )


@main_bp.route("/project/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def project_edit(project_id: int):
    project = _projects.get_by_id(project_id)
    if not project:
        abort(404)
    if project.user_id != current_user.id:
        abort(403)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        stage = (request.form.get("stage") or "").strip().lower()
        support = (request.form.get("support_needed") or "").strip()
        _, err = _svc.update(
            project,
            current_user,
            title,
            description,
            stage,
            support,
        )
        if err:
            return render_template(
                "project_form.html",
                project=project,
                stages=PROJECT_STAGES,
                sidebar_active="project",
                error=err,
            )
        flash("Project updated.", "success")
        return redirect(url_for("main.project_detail", project_id=project_id))
    return render_template(
        "project_form.html",
        project=project,
        stages=PROJECT_STAGES,
        sidebar_active="project",
    )


@main_bp.route("/project/<int:project_id>/complete", methods=["POST"])
@login_required
def project_complete(project_id: int):
    project = _projects.get_by_id(project_id)
    if not project:
        abort(404)
    _, err = _svc.complete(project, current_user)
    if err:
        flash(err, "error")
    else:
        flash("Project marked complete — welcome to the celebration wall.", "success")
    return redirect(url_for("main.project_detail", project_id=project_id))


@main_bp.route("/project/<int:project_id>/comments", methods=["POST"])
@login_required
def project_add_comment(project_id: int):
    project = _projects.get_by_id(project_id)
    if not project:
        abort(404)
    content = (request.form.get("content") or "").strip()
    _, err = _svc.add_comment(project, current_user, content)
    if err:
        flash(err, "error")
    else:
        flash("Comment posted.", "success")
    return redirect(f"{url_for('main.project_detail', project_id=project_id)}#comments")


@main_bp.route("/project/<int:project_id>/milestones", methods=["POST"])
@login_required
def project_add_milestone(project_id: int):
    project = _projects.get_by_id(project_id)
    if not project:
        abort(404)
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    _, err = _svc.add_milestone(project, current_user, title, description)
    if err:
        flash(err, "error")
    else:
        flash("Milestone added.", "success")
    return redirect(f"{url_for('main.project_detail', project_id=project_id)}#milestones")


@main_bp.route("/project/<int:project_id>/collaboration", methods=["POST"])
@login_required
def project_request_collab(project_id: int):
    project = _projects.get_by_id(project_id)
    if not project:
        abort(404)
    message = (request.form.get("message") or "").strip()
    _, err = _svc.request_collaboration(project, current_user, message)
    if err:
        flash(err, "error")
    else:
        flash("Collaboration request sent.", "success")
    return redirect(f"{url_for('main.project_detail', project_id=project_id)}#collaboration")


@main_bp.route("/project/<int:project_id>")
def project_detail(project_id: int):
    project = _projects.get_by_id(project_id)
    if not project:
        abort(404)
    milestones = _projects.list_milestones_ordered(project_id)
    comments = _projects.list_comments(project_id)
    collabs = _projects.list_collaboration_for_project(project_id)
    is_owner = current_user.is_authenticated and current_user.id == project.user_id
    return render_template(
        "project_detail.html",
        project=project,
        milestones=milestones,
        comments=comments,
        collabs=collabs,
        is_owner=is_owner,
        sidebar_active="project",
    )


@main_bp.route("/ssr/feed")
def ssr_feed():
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get("per_page", "20"))
    except ValueError:
        per_page = 20
    stage = (request.args.get("stage") or "").strip().lower()
    if stage and stage not in PROJECT_STAGES:
        stage = ""
    svc = FeedService()
    feed = svc.page(page=page, per_page=per_page, stage=stage or None)
    spotlight = svc.spotlight_newest(k=3)
    html = render_template(
        "feed_ssr.html",
        feed=feed,
        spotlight=spotlight,
        page=max(1, page),
        per_page=per_page,
        stage_filter=stage,
        stages=PROJECT_STAGES,
        nav_active="feed",
        sidebar_active="feed",
    )
    resp = make_response(html)
    resp.headers["X-Mzansi-Template"] = "feed_ssr_v2"
    return resp


@main_bp.route("/celebration")
def ssr_celebration():
    rows = _projects.list_celebration(limit=100)
    return render_template(
        "celebration_ssr.html",
        projects=rows,
        nav_active="celebration",
        sidebar_active="celebration",
    )


@main_bp.route("/system")
def ssr_system():
    snap = _platform.snapshot()
    return render_template(
        "system_ssr.html",
        snap=snap,
        api_version=API_VERSION,
        nav_active="system",
        sidebar_active="system",
    )


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        user = _auth.authenticate(email, password)
        if not user:
            return render_template(
                "login_ssr.html",
                error="Invalid email or password.",
                nav_active="",
            )
        login_user(user)
        nxt = request.args.get("next") or ""
        if nxt.startswith("/") and not nxt.startswith("//"):
            return redirect(nxt)
        return redirect(url_for("main.dashboard"))
    return render_template("login_ssr.html", nav_active="")


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        user, err = _auth.register(name, email, password)
        if err:
            return render_template(
                "register_ssr.html",
                error=err,
                nav_active="",
            )
        login_user(user)
        return redirect(url_for("main.dashboard"))
    return render_template("register_ssr.html", nav_active="")


@main_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@main_bp.route("/projects/status/<string:status>")
def projects_by_status(status: str):
    key = (status or "").strip().lower()
    if key not in ALLOWED_PROJECT_STATUS:
        abort(404)
    rows = (
        db.session.query(Project)
        .options(joinedload(Project.owner))
        .filter(Project.status == key)
        .order_by(Project.created_at.desc())
        .all()
    )
    return render_template(
        "projects_by_status.html",
        status_label=key,
        projects=rows,
        nav_active="feed",
        sidebar_active="feed",
    )


@main_bp.route("/<path:path>")
def catch_all(path: str):
    if path == "api" or path.startswith("api/"):
        return jsonify(
            error="Not found",
            path=request.path,
            hint="JSON API is under /api/v1 (try GET /api/v1).",
        ), 404
    return render_template("not_found.html", path=request.path, nav_active=""), 404
