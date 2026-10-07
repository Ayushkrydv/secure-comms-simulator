from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User, SecurityLog
from app import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    from flask_login import current_user
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            _log(None, "LOGIN_FAILED", f"Failed login attempt for username: '{username}'")
            flash("Invalid credentials. Access denied.", "danger")
            return render_template("login.html")

        if user.status != "active":
            _log(user.id, "LOGIN_BLOCKED", f"Disabled account login attempt: {username}")
            flash("Account is disabled. Contact administrator.", "warning")
            return render_template("login.html")

        login_user(user)
        _log(user.id, "LOGIN_SUCCESS", f"User '{username}' authenticated successfully.")
        return _redirect_by_role(user.role)

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    _log(current_user.id, "LOGOUT", f"User '{current_user.username}' logged out.")
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


def _redirect_by_role(role):
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "command":
        return redirect(url_for("command.dashboard"))
    return redirect(url_for("field.dashboard"))


def _log(user_id, event_type, description):
    entry = SecurityLog(user_id=user_id, event_type=event_type, description=description)
    db.session.add(entry)
    db.session.commit()
