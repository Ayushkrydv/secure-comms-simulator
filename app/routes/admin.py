from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User, Message, SecurityLog, NetworkEvent
from app import db, network
from datetime import datetime, timezone

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route("/dashboard")
@login_required
@_require_admin
def dashboard():
    net = network.get_state()
    users = User.query.order_by(User.created_at.desc()).all()
    logs = SecurityLog.query.order_by(SecurityLog.timestamp.desc()).limit(30).all()
    total_messages = Message.query.count()
    queued = Message.query.filter_by(status="queued").count()
    delivered = Message.query.filter_by(status="delivered").count()
    rejected = Message.query.filter_by(status="rejected").count()
    stats = {"total": total_messages, "delivered": delivered, "queued": queued, "rejected": rejected}
    return render_template(
        "admin_dashboard.html",
        net=net,
        users=users,
        logs=logs,
        stats=stats,
    )


@admin_bp.route("/users/create", methods=["POST"])
@login_required
@_require_admin
def create_user():
    username = request.form.get("username", "").strip()
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "field")
    password = request.form.get("password", "")

    if not username or not name or not password:
        flash("All fields are required.", "warning")
        return redirect(url_for("admin.dashboard"))

    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' already exists.", "danger")
        return redirect(url_for("admin.dashboard"))

    u = User(
        username=username,
        name=name,
        role=role,
        password_hash=generate_password_hash(password),
        status="active",
    )
    db.session.add(u)
    _log(current_user.id, "USER_CREATED", f"Admin created user '{username}' with role '{role}'.")
    db.session.commit()
    flash(f"User '{username}' created successfully.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@_require_admin
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Cannot disable your own account.", "warning")
        return redirect(url_for("admin.dashboard"))
    user.status = "disabled" if user.status == "active" else "active"
    action = "DISABLED" if user.status == "disabled" else "ENABLED"
    _log(current_user.id, f"USER_{action}", f"Admin {action.lower()} account '{user.username}'.")
    db.session.commit()
    flash(f"Account '{user.username}' is now {user.status}.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/network/set", methods=["POST"])
@login_required
@_require_admin
def set_network():
    state = request.form.get("network_state", "NORMAL")
    latency = request.form.get("latency", 0, type=int)
    packet_loss = request.form.get("packet_loss", 0, type=int)
    network.set_state(state, latency, packet_loss)

    # Persist to DB for audit trail
    ev = NetworkEvent(network_state=state, latency=latency, packet_loss=packet_loss)
    db.session.add(ev)
    _log(current_user.id, "NETWORK_CHANGE", f"Network set to {state} | latency={latency}ms | loss={packet_loss}%")
    db.session.commit()

    # If restoring, attempt to flush queued messages
    if state != "OFFLINE":
        _flush_queue()

    flash(f"Network simulation set to {state}.", "info")
    return redirect(url_for("admin.dashboard"))


def _flush_queue():
    """Attempt delivery of all queued messages when network is restored."""
    from app import security as sec
    queued_msgs = Message.query.filter_by(status="queued").all()
    flushed = 0
    for msg in queued_msgs:
        result = network.simulate_transmission()
        if result["delivered"]:
            # Verify integrity before marking delivered
            ts = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ok = sec.verify_integrity_tag(
                msg.message_id, msg.sender_id, msg.receiver_id, ts,
                msg.encrypted_content, msg.integrity_tag
            )
            if ok:
                if sec.is_replay(msg.message_id):
                    msg.status = "rejected"
                    _log(None, "REPLAY_DETECTED", f"Queued msg {msg.message_id} is a replay — rejected.")
                else:
                    msg.status = "delivered"
                    msg.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    sec.mark_processed(msg.message_id)
                    flushed += 1
            else:
                msg.status = "rejected"
                _log(None, "INTEGRITY_FAIL", f"Queued msg {msg.message_id} failed integrity check — rejected.")
    db.session.commit()
    if flushed:
        _log(None, "QUEUE_FLUSHED", f"Network restored. {flushed} queued message(s) delivered.")


def _log(user_id, event_type, description):
    entry = SecurityLog(user_id=user_id, event_type=event_type, description=description)
    db.session.add(entry)
    db.session.commit()
