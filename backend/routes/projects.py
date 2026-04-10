from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from backend.forms import (
    CollaborateForm,
    CommentForm,
    CompleteProjectForm,
    MilestoneForm,
    ProjectForm,
)
from backend.repositories.project_repository import ProjectRepository
from backend.services.project_service import ProjectService

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")
_repo = ProjectRepository()
_svc = ProjectService()


@projects_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project, err = _svc.create(
            current_user,
            form.title.data,
            form.description.data or "",
            form.stage.data,
            form.support_needed.data or "",
        )
        if err:
            flash(err, "danger")
        else:
            flash("Project published to the feed.", "success")
            return redirect(url_for("projects.detail", project_id=project.id))
    return render_template("project_new.html", form=form)


@projects_bp.route("/<int:project_id>")
def detail(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        abort(404)

    comment_f = CommentForm()
    collab_f = CollaborateForm()
    milestone_f = MilestoneForm()
    complete_f = CompleteProjectForm()

    read_only = not current_user.is_authenticated

    return render_template(
        "project_detail.html",
        project=project,
        milestones=_repo.list_milestones_ordered(project.id),
        comments=_repo.list_comments(project.id),
        collabs=_repo.list_collaboration_for_project(project.id),
        comment_f=comment_f,
        collab_f=collab_f,
        milestone_f=milestone_f,
        complete_f=complete_f,
        read_only=read_only,
    )


@projects_bp.route("/<int:project_id>/comments", methods=["POST"])
@login_required
def post_comment(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        abort(404)
    form = CommentForm()
    if form.validate_on_submit():
        _, err = _svc.add_comment(project, current_user, form.content.data)
        if err:
            flash(err, "danger")
        else:
            flash("Comment added.", "success")
    else:
        flash("Could not post that comment. Check length and try again.", "danger")
    return redirect(url_for("projects.detail", project_id=project_id))


@projects_bp.route("/<int:project_id>/collaborate", methods=["POST"])
@login_required
def post_collaborate(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        abort(404)
    form = CollaborateForm()
    if form.validate_on_submit():
        _, err = _svc.request_collaboration(project, current_user, form.message.data or "")
        if err:
            flash(err, "danger")
        else:
            flash("Collaboration request sent.", "success")
    return redirect(url_for("projects.detail", project_id=project_id))


@projects_bp.route("/<int:project_id>/milestones", methods=["POST"])
@login_required
def post_milestone(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        abort(404)
    form = MilestoneForm()
    if form.validate_on_submit():
        _, err = _svc.add_milestone(
            project, current_user, form.title.data, form.description.data or ""
        )
        if err:
            flash(err, "danger")
        else:
            flash("Milestone recorded.", "success")
    else:
        flash("Please give the milestone a short title.", "danger")
    return redirect(url_for("projects.detail", project_id=project_id))


@projects_bp.route("/<int:project_id>/complete", methods=["POST"])
@login_required
def post_complete(project_id: int):
    project = _repo.get_by_id(project_id)
    if not project:
        abort(404)
    form = CompleteProjectForm()
    if form.validate_on_submit():
        _, err = _svc.complete(project, current_user)
        if err:
            flash(err, "danger")
        else:
            flash("Project completed. It will show on the Celebration Wall.", "success")
    return redirect(url_for("projects.detail", project_id=project_id))
