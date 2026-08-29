from __future__ import annotations

import hashlib
import hmac
import os


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
