from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from backend.forms import ProfileForm
from backend.repositories.user_repository import UserRepository
from backend.services.feed_service import FeedService

main_bp = Blueprint("main", __name__)
_feed = FeedService()
_users = UserRepository()


@main_bp.route("/")
def home():
    return redirect(url_for("main.feed"))


@main_bp.route("/feed")
def feed():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    result = _feed.page(page=page, per_page=10)
    return render_template("feed.html", feed=result)


@main_bp.route("/celebration")
def celebration():
    from backend.repositories.project_repository import ProjectRepository

    repo = ProjectRepository()
    completed = repo.list_celebration(limit=200)
    return render_template("celebration.html", projects=completed)


@main_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        _users.update_profile(current_user, form.name.data, form.bio.data)
        flash("Profile updated.", "success")
        return redirect(url_for("main.account"))
    return render_template("account.html", form=form)
