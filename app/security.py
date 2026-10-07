"""
security.py — Cryptographic helpers for the Secure Comms Simulator.

Uses:
  - Fernet (AES-128-CBC + HMAC-SHA256) for authenticated symmetric encryption.
  - HMAC-SHA256 for per-message integrity tags.
  - In-memory set for replay-attack detection (resets on server restart; fine for prototype).
"""

import os
import hmac
import hashlib
import base64
from cryptography.fernet import Fernet

# ---------------------------------------------------------------------------
# Shared symmetric key — in production this would be exchanged via PKI.
# Stored as an env-var so it survives restarts without being hard-coded.
# ---------------------------------------------------------------------------
_RAW_KEY = os.environ.get("COMMS_FERNET_KEY", None)
if _RAW_KEY:
    FERNET_KEY = _RAW_KEY.encode()
else:
    FERNET_KEY = Fernet.generate_key()          # ephemeral for dev/demo

_fernet = Fernet(FERNET_KEY)

# ---------------------------------------------------------------------------
# Replay-attack detection: store processed message IDs.
# ---------------------------------------------------------------------------
_processed_ids: set[str] = set()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encrypt_message(plaintext: str) -> str:
    """Return base64 Fernet token (already includes IV + HMAC internally)."""
    token = _fernet.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_message(token: str) -> str:
    """Decrypt a Fernet token; raises InvalidToken on tampering."""
    plaintext = _fernet.decrypt(token.encode("utf-8"))
    return plaintext.decode("utf-8")


def compute_integrity_tag(message_id: str, sender_id: int, receiver_id: int,
                           timestamp: str, encrypted_content: str) -> str:
    """HMAC-SHA256 over the canonical message envelope fields."""
    material = f"{message_id}|{sender_id}|{receiver_id}|{timestamp}|{encrypted_content}"
    tag = hmac.new(FERNET_KEY, material.encode("utf-8"), hashlib.sha256).hexdigest()
    return tag


def verify_integrity_tag(message_id: str, sender_id: int, receiver_id: int,
                          timestamp: str, encrypted_content: str, tag: str) -> bool:
    expected = compute_integrity_tag(message_id, sender_id, receiver_id, timestamp, encrypted_content)
    return hmac.compare_digest(expected, tag)


def is_replay(message_id: str) -> bool:
    """Return True if this message_id has already been processed (replay detected)."""
    return message_id in _processed_ids


def mark_processed(message_id: str) -> None:
    _processed_ids.add(message_id)
