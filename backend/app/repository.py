"""Single import point for user/recording persistence.

Uses Supabase Postgres (BW_users, BW_recordings) once backend/.env has a real
SUPABASE_DB_PASSWORD. Until then, falls back to a local JSON file so the app
keeps working end-to-end for local testing.
"""
from __future__ import annotations

from typing import Any

from .auth import hash_password
from .config import ADMIN_PASSWORD, ADMIN_USERNAME
from .db import repository as pg
from .db.connection import ensure_schema, is_configured
from . import local_store as local


def _impl():
    return pg if is_configured() else local


def init() -> None:
    """Ensures schema + a default admin user exist. Safe to call multiple times."""
    ensure_schema()
    impl = _impl()
    if impl.get_user_by_username(ADMIN_USERNAME) is None:
        impl.create_user(ADMIN_USERNAME, hash_password(ADMIN_PASSWORD))


def get_user_by_username(username: str) -> dict[str, Any] | None:
    return _impl().get_user_by_username(username)


def create_recording(
    user_id: int, original_filename: str, title: str, recorded_at: str | None, audio_path: str
) -> dict[str, Any]:
    return _impl().create_recording(user_id, original_filename, title, recorded_at, audio_path)


def update_recording_status(
    recording_id: int, status: str, transcript_path: str | None = None, error: str | None = None
) -> dict[str, Any] | None:
    return _impl().update_recording_status(recording_id, status, transcript_path, error)


def list_recordings(user_id: int) -> list[dict[str, Any]]:
    return _impl().list_recordings(user_id)


def get_recording(recording_id: int, user_id: int) -> dict[str, Any] | None:
    return _impl().get_recording(recording_id, user_id)
