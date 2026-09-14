from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time


def hash_password(password: str, salt: str | None = None) -> str:
    active_salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), active_salt.encode("utf-8"), 120_000).hex()
    return f"pbkdf2_sha256${active_salt}${digest}"


def verify_password(password: str, stored_password: str) -> bool:
    if not stored_password.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(password, stored_password)
    _, salt, expected = stored_password.split("$", 2)
    candidate = hash_password(password, salt).split("$", 2)[2]
    return hmac.compare_digest(candidate, expected)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_session_token(username: str, role: str, secret_key: str, ttl_seconds: int) -> str:
    """Stateless, signed token — no database/session table required."""
    payload = json.dumps({"username": username, "role": role, "exp": int(time.time()) + ttl_seconds}).encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), payload, hashlib.sha256).digest()
    return f"{_b64encode(payload)}.{_b64encode(signature)}"


def verify_session_token(token: str, secret_key: str) -> dict[str, object] | None:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
        payload = _b64decode(payload_b64)
        expected_signature = hmac.new(secret_key.encode("utf-8"), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(_b64decode(signature_b64), expected_signature):
            return None
        data = json.loads(payload)
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    if data.get("exp", 0) < time.time():
        return None
    return data

