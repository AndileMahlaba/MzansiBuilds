from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from backend.extensions import db
from backend.forms import LoginForm, RegisterForm
from backend.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="")
_auth = AuthService()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    form = RegisterForm()
    if form.validate_on_submit():
        user, err = _auth.register(form.name.data, form.email.data, form.password.data)
        if err:
            flash(err, "danger")
        else:
            login_user(user)
            flash("Welcome to MzansiBuilds.", "success")
            return redirect(url_for("main.feed"))
    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    form = LoginForm()
    if form.validate_on_submit():
        user = _auth.authenticate(form.email.data, form.password.data)
        if not user:
            flash("Email or password did not match.", "danger")
        else:
            login_user(user)
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("main.feed"))
    return render_template("login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("auth.login"))
