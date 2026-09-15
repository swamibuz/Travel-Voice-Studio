"""JSON-file-backed fallback store, used only until Supabase credentials are set
in backend/.env. Mirrors the function signatures in app.db.repository so the rest
of the app doesn't need to know which backend is active.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .config import DATA_DIR

_LOCK = threading.Lock()
_STORE_PATH = DATA_DIR / "local_store.json"


def _load() -> dict[str, Any]:
    if not _STORE_PATH.exists():
        return {"users": [], "recordings": [], "next_user_id": 1, "next_recording_id": 1}
    return json.loads(_STORE_PATH.read_text(encoding="utf-8"))


def _save(data: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with _LOCK:
        data = _load()
    for user in data["users"]:
        if user["username"] == username:
            return user
    return None


def create_user(username: str, password_hash: str) -> dict[str, Any]:
    with _LOCK:
        data = _load()
        existing = next((u for u in data["users"] if u["username"] == username), None)
        if existing:
            return existing
        user = {"id": data["next_user_id"], "username": username, "password_hash": password_hash}
        data["users"].append(user)
        data["next_user_id"] += 1
        _save(data)
        return user


def create_recording(
    user_id: int, original_filename: str, title: str, recorded_at: str | None, audio_path: str
) -> dict[str, Any]:
    with _LOCK:
        data = _load()
        recording = {
            "id": data["next_recording_id"],
            "user_id": user_id,
            "original_filename": original_filename,
            "title": title,
            "recorded_at": recorded_at,
            "status": "uploaded",
            "audio_path": audio_path,
            "transcript_path": None,
            "error": None,
        }
        data["recordings"].append(recording)
        data["next_recording_id"] += 1
        _save(data)
        return recording


def update_recording_status(
    recording_id: int, status: str, transcript_path: str | None = None, error: str | None = None
) -> dict[str, Any] | None:
    with _LOCK:
        data = _load()
        for recording in data["recordings"]:
            if recording["id"] == recording_id:
                recording["status"] = status
                if transcript_path is not None:
                    recording["transcript_path"] = transcript_path
                recording["error"] = error
                _save(data)
                return recording
    return None


def list_recordings(user_id: int) -> list[dict[str, Any]]:
    with _LOCK:
        data = _load()
    items = [r for r in data["recordings"] if r["user_id"] == user_id]
    return list(reversed(items))


def get_recording(recording_id: int, user_id: int) -> dict[str, Any] | None:
    with _LOCK:
        data = _load()
    for recording in data["recordings"]:
        if recording["id"] == recording_id and recording["user_id"] == user_id:
            return recording
    return None
