from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import User, Message, SecurityLog, NetworkEvent
from app import db, network

command_bp = Blueprint("command", __name__, url_prefix="/command")


def _require_command(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user.role not in ("command", "admin"):
            flash("Unauthorised access.", "danger")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


@command_bp.route("/dashboard")
@login_required
@_require_command
def dashboard():
    net = network.get_state()
    users = User.query.filter(User.status == "active").all()
    total_messages = Message.query.count()
    delivered = Message.query.filter_by(status="delivered").count()
    queued = Message.query.filter_by(status="queued").count()
    rejected = Message.query.filter_by(status="rejected").count()
    recent_logs = (
        SecurityLog.query
        .order_by(SecurityLog.timestamp.desc())
        .limit(15)
        .all()
    )
    recent_messages = (
        Message.query
        .order_by(Message.timestamp.desc())
        .limit(20)
        .all()
    )
    stats = {
        "total": total_messages,
        "delivered": delivered,
        "queued": queued,
        "rejected": rejected,
    }
    return render_template(
        "command_dashboard.html",
        net=net,
        users=users,
        stats=stats,
        recent_logs=recent_logs,
        recent_messages=recent_messages,
    )
