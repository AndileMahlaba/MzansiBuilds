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
from backend.extensions import db, limiter
from backend.utils.security import safe_redirect_path
from backend.services.email_delivery import send_password_reset_email, send_verification_email
from backend.utils.smtp_mail import mail_is_configured
from backend.utils.tokens import (
    load_email_verify_token,
    load_password_reset_token,
    make_password_reset_token,
)
from backend.models.project import Project
from backend.repositories.platform_repository import PlatformRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.user_repository import UserRepository
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

def _must_be_verified():
    if current_user.is_authenticated and not getattr(current_user, "email_verified", True):
        flash("Verify your email to use the workspace and projects. Check your inbox for the link.", "error")
        return redirect(url_for("main.register_pending"))
    return None


def _stage_bar_max(snap) -> int:
    m = max(snap.stage_counts.values(), default=0)
    return m if m > 0 else 1


def _busiest_stage_line(snap) -> tuple[str | None, str | None]:
    """Short headline + subline for the pulse page (no stack jargon)."""
    active = [(s, n) for s, n in snap.stage_counts.items() if n > 0]
    if not active:
        return None, None
    stage, n = max(active, key=lambda x: x[1])
    sub = f"{n} open build{'s' if n != 1 else ''} · liveliest stage on the feed right now."
    return stage, sub


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
    redir = _must_be_verified()
    if redir:
        return redir
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
    redir = _must_be_verified()
    if redir:
        return redir
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        bio = (request.form.get("bio") or "")[:500]
        profile_public = request.form.get("profile_public") == "1"
        if name:
            _users.update_profile(
                current_user,
                name,
                bio,
                profile_public=profile_public,
            )
            db.session.refresh(current_user)
            flash("Profile updated.", "success")
        return redirect(url_for("main.account"))
    return render_template("account_ssr.html", sidebar_active="account")


@main_bp.route("/account/password", methods=["POST"])
@login_required
@limiter.limit(
    "10 per minute",
    methods=["POST"],
    error_message="Too many password attempts. Please wait.",
)
def account_password():
    redir = _must_be_verified()
    if redir:
        return redir
    current_pw = request.form.get("current_password") or ""
    new_pw = request.form.get("new_password") or ""
    confirm = request.form.get("confirm_password") or ""
    if new_pw != confirm:
        flash("New passwords do not match.", "error")
        return redirect(url_for("main.account"))
    err = _users.change_password(current_user, current_pw, new_pw)
    if err:
        flash(err, "error")
    else:
        flash("Password updated.", "success")
    return redirect(url_for("main.account"))


@main_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit(
    "8 per minute",
    methods=["POST"],
    error_message="Too many reset requests. Please wait.",
)
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        user = _users.get_by_email(email) if email else None
        if user:
            current_app.logger.info("Password reset requested for user_id=%s", user.id)
            if mail_is_configured(current_app):
                ok, _err = send_password_reset_email(user)
                flash(
                    "If that email is registered, check your inbox for a reset link."
                    if ok
                    else "Could not send email. Try again later or contact support.",
                    "success" if ok else "error",
                )
            else:
                path = url_for("main.reset_password", token=make_password_reset_token(current_app.config["SECRET_KEY"], user.id, user.email))
                if current_app.debug:
                    flash(
                        f"Dev (no SMTP): open {request.url_root.rstrip('/')}{path} to set a new password.",
                        "info",
                    )
                else:
                    flash(
                        "Password reset by email is not configured on this server. "
                        "Set MAIL_SERVER and related variables, or ask an administrator.",
                        "success",
                    )
        else:
            flash("If that email is registered, you will receive reset instructions.", "success")
        return redirect(url_for("main.login"))
    return render_template("forgot_password_ssr.html", nav_active="")


@main_bp.route("/reset-password", methods=["GET", "POST"])
@limiter.limit(
    "10 per minute",
    methods=["POST"],
    error_message="Too many attempts. Please wait.",
)
def reset_password():
    token = (request.args.get("token") or request.form.get("token") or "").strip()
    payload = load_password_reset_token(current_app.config["SECRET_KEY"], token) if token else None

    if request.method == "POST":
        if not payload:
            flash("This reset link is invalid or has expired.", "error")
            return redirect(url_for("main.forgot_password"))
        new_pw = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        if new_pw != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("main.reset_password", token=token))
        uid = int(payload["uid"])
        user = _users.get_by_id(uid)
        if not user:
            flash("Account not found.", "error")
            return redirect(url_for("main.login"))
        try:
            _users.apply_new_password(user, new_pw)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("main.reset_password", token=token))
        login_user(user)
        flash("Your password has been updated. You are now signed in.", "success")
        return redirect(url_for("main.dashboard"))

    if not payload:
        return render_template("reset_password_ssr.html", invalid=True, nav_active="")
    return render_template("reset_password_ssr.html", invalid=False, token=token, nav_active="")


@main_bp.route("/verify-email")
def verify_email():
    token = (request.args.get("token") or "").strip()
    payload = load_email_verify_token(current_app.config["SECRET_KEY"], token) if token else None
    if not payload:
        flash("That confirmation link is invalid or has expired.", "error")
        return redirect(url_for("main.login"))
    user = _users.get_by_id(int(payload["uid"]))
    if not user or (payload.get("email") or "").lower() != user.email.lower():
        flash("That confirmation link is invalid.", "error")
        return redirect(url_for("main.login"))
    _users.mark_email_verified(user)
    flash("Email confirmed. You can sign in now.", "success")
    return redirect(url_for("main.login"))


@main_bp.route("/register/check-email")
def register_pending():
    email = (request.args.get("email") or "").strip()
    return render_template("register_pending_ssr.html", email=email, nav_active="")


@main_bp.route("/resend-verification", methods=["POST"])
@limiter.limit(
    "5 per minute",
    methods=["POST"],
    error_message="Too many resend attempts. Please wait.",
)
def resend_verification():
    email = (request.form.get("email") or "").strip()
    user = _users.get_by_email(email) if email else None
    if user and not user.email_verified:
        send_verification_email(user)
    flash(
        "If that email is registered and still pending, we sent a new confirmation link.",
        "success",
    )
    return redirect(url_for("main.login"))


@main_bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    redir = _must_be_verified()
    if redir:
        return redir
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        stage = (request.form.get("stage") or "").strip().lower()
        support = (request.form.get("support_needed") or "").strip()
        repo_url = (request.form.get("repo_url") or "").strip()
        demo_url = (request.form.get("demo_url") or "").strip()
        proj, err = _svc.create(
            current_user, title, description, stage, support, repo_url=repo_url, demo_url=demo_url
        )
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
    redir = _must_be_verified()
    if redir:
        return redir
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        stage = (request.form.get("stage") or "").strip().lower()
        support = (request.form.get("support_needed") or "").strip()
        repo_url = (request.form.get("repo_url") or "").strip()
        demo_url = (request.form.get("demo_url") or "").strip()
        _, err = _svc.update(
            project,
            current_user,
            title,
            description,
            stage,
            support,
            repo_url=repo_url,
            demo_url=demo_url,
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
    redir = _must_be_verified()
    if redir:
        return redir
    project = _projects.get_by_id(project_id)
    if not project:
        abort(404)
    _, err = _svc.complete(project, current_user)
    if err:
        flash(err, "error")
    else:
        flash("Project marked complete. Welcome to the celebration wall.", "success")
    return redirect(url_for("main.project_detail", project_id=project_id))


@main_bp.route("/project/<int:project_id>/comments", methods=["POST"])
@login_required
def project_add_comment(project_id: int):
    redir = _must_be_verified()
    if redir:
        return redir
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
    redir = _must_be_verified()
    if redir:
        return redir
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


@main_bp.route("/project/<int:project_id>/build-log", methods=["POST"])
@login_required
def project_add_build_log(project_id: int):
    redir = _must_be_verified()
    if redir:
        return redir
    project = _projects.get_by_id(project_id)
    if not project:
        abort(404)
    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    _, err = _svc.add_build_log(project, current_user, title, body)
    if err:
        flash(err, "error")
    else:
        flash("Build update posted.", "success")
    return redirect(f"{url_for('main.project_detail', project_id=project_id)}#build-log")


@main_bp.route("/project/<int:project_id>/collaboration", methods=["POST"])
@login_required
def project_request_collab(project_id: int):
    redir = _must_be_verified()
    if redir:
        return redir
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
    build_logs = _projects.list_build_logs(project_id)
    comments = _projects.list_comments(project_id)
    collabs = _projects.list_collaboration_for_project(project_id)
    is_owner = current_user.is_authenticated and current_user.id == project.user_id
    return render_template(
        "project_detail.html",
        project=project,
        milestones=milestones,
        build_logs=build_logs,
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
    pulse = _platform.snapshot()
    busiest_stage, busiest_detail = _busiest_stage_line(pulse)
    recent_comments = _platform.recent_comments(limit=6)
    html = render_template(
        "feed_ssr.html",
        feed=feed,
        spotlight=spotlight,
        pulse=pulse,
        stage_bar_max=_stage_bar_max(pulse),
        busiest_stage=busiest_stage,
        busiest_detail=busiest_detail,
        recent_comments=recent_comments,
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
    pulse = _platform.snapshot()
    return render_template(
        "celebration_ssr.html",
        projects=rows,
        pulse=pulse,
        completed_total=pulse.completed_projects,
        nav_active="celebration",
        sidebar_active="celebration",
    )


@main_bp.route("/system")
def ssr_system():
    snap = _platform.snapshot()
    insight_stage, insight_detail = _busiest_stage_line(snap)
    return render_template(
        "system_ssr.html",
        snap=snap,
        stage_bar_max=_stage_bar_max(snap),
        insight_stage=insight_stage,
        insight_detail=insight_detail,
        nav_active="system",
        sidebar_active="system",
    )


@main_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(
    "20 per minute",
    methods=["POST"],
    error_message="Too many login attempts. Please wait a moment.",
)
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
        if not getattr(user, "email_verified", True):
            return render_template(
                "login_ssr.html",
                error="Confirm your email before signing in. Check your inbox, or use resend on the check-email page.",
                nav_active="",
                pending_email=email,
            )
        login_user(user)
        nxt = safe_redirect_path(request.args.get("next"))
        if nxt:
            return redirect(nxt)
        return redirect(url_for("main.dashboard"))
    return render_template("login_ssr.html", nav_active="")


@main_bp.route("/register", methods=["GET", "POST"])
@limiter.limit(
    "15 per minute",
    methods=["POST"],
    error_message="Too many registration attempts. Please wait a moment.",
)
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        need_verify = bool(current_app.config.get("EMAIL_VERIFICATION_REQUIRED", True))
        user, err = _auth.register(
            name, email, password, email_verified=not need_verify
        )
        if err:
            return render_template(
                "register_ssr.html",
                error=err,
                nav_active="",
            )
        if need_verify:
            send_verification_email(user)
            return redirect(url_for("main.register_pending", email=user.email))
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
