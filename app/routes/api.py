"""
api.py — JSON API endpoints used by dashboard polling and replay-attack demo.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import Message, SecurityLog, User
from app import db, network, security
from datetime import datetime

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/network/status")
@login_required
def network_status():
    return jsonify(network.get_state())


@api_bp.route("/stats")
@login_required
def stats():
    total = Message.query.count()
    delivered = Message.query.filter_by(status="delivered").count()
    queued = Message.query.filter_by(status="queued").count()
    rejected = Message.query.filter_by(status="rejected").count()
    active_users = User.query.filter_by(status="active").count()
    return jsonify({
        "total": total,
        "delivered": delivered,
        "queued": queued,
        "rejected": rejected,
        "active_users": active_users,
    })


@api_bp.route("/messages/mine")
@login_required
def my_messages():
    msgs = (
        Message.query
        .filter(
            (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
        )
        .order_by(Message.timestamp.desc())
        .limit(20)
        .all()
    )
    return jsonify([m.to_dict() for m in msgs])


@api_bp.route("/replay/test", methods=["POST"])
@login_required
def replay_test():
    """
    Demo endpoint: submit an existing message_id to trigger replay detection.
    Body JSON: {"message_id": "<uuid>"}
    """
    data = request.get_json(silent=True) or {}
    msg_id = data.get("message_id", "").strip()

    if not msg_id:
        return jsonify({"error": "message_id required"}), 400

    msg = Message.query.filter_by(message_id=msg_id).first()
    if not msg:
        return jsonify({"error": "Message not found"}), 404

    if security.is_replay(msg_id):
        entry = SecurityLog(
            user_id=current_user.id,
            event_type="REPLAY_DETECTED",
            description=f"Duplicate message ID {msg_id} submitted by {current_user.username} — rejected.",
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"status": "REJECTED", "reason": "Replay detected — duplicate message ID", "message_id": msg_id})

    # Mark it as processed and check integrity
    ts = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    ok = security.verify_integrity_tag(
        msg.message_id, msg.sender_id, msg.receiver_id, ts,
        msg.encrypted_content, msg.integrity_tag
    )
    if not ok:
        entry = SecurityLog(
            user_id=current_user.id,
            event_type="INTEGRITY_FAIL",
            description=f"Message {msg_id} failed integrity check.",
        )
        db.session.add(entry)
        db.session.commit()
        msg.status = "rejected"
        db.session.commit()
        return jsonify({"status": "REJECTED", "reason": "Integrity verification failed", "message_id": msg_id})

    security.mark_processed(msg_id)
    return jsonify({"status": "ACCEPTED", "message_id": msg_id})


@api_bp.route("/logs/recent")
@login_required
def recent_logs():
    if current_user.role not in ("admin", "command"):
        return jsonify({"error": "Unauthorised"}), 403
    logs = SecurityLog.query.order_by(SecurityLog.timestamp.desc()).limit(20).all()
    return jsonify([l.to_dict() for l in logs])
