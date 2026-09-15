"""Audio + transcript file storage on local disk. Only file paths are ever
recorded in the database — the audio bytes and transcript text itself never
go into a database column.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from .config import AUDIO_STORAGE_DIR, TRANSCRIPT_STORAGE_DIR


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    return re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-") or "recording"


def save_audio(user_id: int, filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix or ".m4a"
    unique_name = f"{_safe_stem(filename)}-{uuid.uuid4().hex[:8]}{suffix}"
    user_dir = AUDIO_STORAGE_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / unique_name
    path.write_bytes(content)
    return str(path)


def save_transcript(user_id: int, recording_id: int, text: str) -> str:
    user_dir = TRANSCRIPT_STORAGE_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / f"{recording_id}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def read_transcript(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")
