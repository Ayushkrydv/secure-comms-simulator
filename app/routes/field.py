from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import User, Message, SecurityLog
from app import db
from app import security, network
from datetime import datetime, timezone
import uuid

field_bp = Blueprint("field", __name__, url_prefix="/field")


def _require_field(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user.role not in ("field", "command", "admin"):
            flash("Unauthorised access.", "danger")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


@field_bp.route("/dashboard")
@login_required
@_require_field
def dashboard():
    contacts = User.query.filter(
        User.id != current_user.id,
        User.status == "active"
    ).all()
    net = network.get_state()
    pending = Message.query.filter_by(sender_id=current_user.id, status="queued").count()
    my_messages = (
        Message.query
        .filter(
            (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
        )
        .order_by(Message.timestamp.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "field_dashboard.html",
        contacts=contacts,
        net=net,
        pending=pending,
        messages=my_messages,
    )


@field_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    receiver_id = request.form.get("receiver_id", type=int)
    plaintext = request.form.get("message", "").strip()

    if not receiver_id or not plaintext:
        flash("Recipient and message are required.", "warning")
        return redirect(url_for("field.dashboard"))

    receiver = User.query.get(receiver_id)
    if not receiver or receiver.status != "active":
        flash("Invalid recipient.", "danger")
        return redirect(url_for("field.dashboard"))

    # Build envelope
    msg_id = str(uuid.uuid4())
    timestamp_str = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
    encrypted = security.encrypt_message(plaintext)
    tag = security.compute_integrity_tag(msg_id, current_user.id, receiver_id, timestamp_str, encrypted)

    # Simulate network
    result = network.simulate_transmission()

    if result["delivered"]:
        status = "delivered"
        security.mark_processed(msg_id)
        _log(current_user.id, "MSG_SENT", f"Message {msg_id} delivered to {receiver.username}. {result['reason']}")
    else:
        status = "queued"
        _log(current_user.id, "MSG_QUEUED", f"Message {msg_id} queued (offline/loss). Reason: {result['reason']}")

    msg = Message(
        message_id=msg_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        encrypted_content=encrypted,
        integrity_tag=tag,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        status=status,
        queued_offline=(status == "queued"),
    )
    db.session.add(msg)
    db.session.commit()

    if status == "delivered":
        flash(f"✅ Message encrypted and delivered. ({result['reason']})", "success")
    else:
        flash(f"📦 Network unavailable. Message securely queued. ({result['reason']})", "warning")

    return redirect(url_for("field.dashboard"))


def _log(user_id, event_type, description):
    entry = SecurityLog(user_id=user_id, event_type=event_type, description=description)
    db.session.add(entry)
    db.session.commit()
