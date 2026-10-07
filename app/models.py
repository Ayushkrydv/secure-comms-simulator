from datetime import datetime, timezone

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), nullable=False)  # field | command | admin
    password_hash = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(16), default="active")  # active | disabled
    created_at = db.Column(db.DateTime, default=_utcnow)

    sent_messages = db.relationship("Message", foreign_keys="Message.sender_id", backref="sender", lazy="dynamic")
    received_messages = db.relationship("Message", foreign_keys="Message.receiver_id", backref="receiver", lazy="dynamic")

    def is_active(self):
        return self.status == "active"

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(64), unique=True, nullable=False)  # UUID
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    encrypted_content = db.Column(db.Text, nullable=False)
    integrity_tag = db.Column(db.String(256), nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)
    status = db.Column(db.String(16), default="queued")  # queued | delivered | rejected
    queued_offline = db.Column(db.Boolean, default=False)
    delivered_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "sender": self.sender.name if self.sender else "Unknown",
            "receiver": self.receiver.name if self.receiver else "Unknown",
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "queued_offline": self.queued_offline,
        }


class NetworkEvent(db.Model):
    __tablename__ = "network_events"
    id = db.Column(db.Integer, primary_key=True)
    network_state = db.Column(db.String(16), nullable=False)  # NORMAL | DEGRADED | OFFLINE
    latency = db.Column(db.Integer, default=0)       # ms
    packet_loss = db.Column(db.Integer, default=0)   # percent
    timestamp = db.Column(db.DateTime, default=_utcnow)


class SecurityLog(db.Model):
    __tablename__ = "security_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    event_type = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", backref="security_logs")

    def to_dict(self):
        return {
            "log_id": self.id,
            "user": self.user.username if self.user else "SYSTEM",
            "event_type": self.event_type,
            "description": self.description,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
