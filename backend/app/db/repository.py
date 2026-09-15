from __future__ import annotations

from datetime import datetime
from typing import Any

from .connection import get_connection


def _row_to_user(row: tuple) -> dict[str, Any]:
    return {"id": row[0], "username": row[1], "password_hash": row[2]}


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, username, password_hash FROM "BW_users" WHERE username = %s',
                (username,),
            )
            row = cur.fetchone()
    return _row_to_user(row) if row else None


def create_user(username: str, password_hash: str) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO "BW_users" (username, password_hash) VALUES (%s, %s) '
                "ON CONFLICT (username) DO NOTHING RETURNING id, username, password_hash",
                (username, password_hash),
            )
            row = cur.fetchone()
    if row:
        return _row_to_user(row)
    return get_user_by_username(username)  # type: ignore[return-value]


def _row_to_recording(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "user_id": row[1],
        "original_filename": row[2],
        "title": row[3],
        "recorded_at": row[4].isoformat() if isinstance(row[4], datetime) else row[4],
        "status": row[5],
        "audio_path": row[6],
        "transcript_path": row[7],
        "error": row[8],
    }


_RECORDING_COLUMNS = (
    "id, user_id, original_filename, title, recorded_at, status, audio_path, transcript_path, error"
)


def create_recording(
    user_id: int, original_filename: str, title: str, recorded_at: str | None, audio_path: str
) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f'INSERT INTO "BW_recordings" '
                "(user_id, original_filename, title, recorded_at, status, audio_path) "
                "VALUES (%s, %s, %s, %s, 'uploaded', %s) RETURNING {cols}".format(cols=_RECORDING_COLUMNS),
                (user_id, original_filename, title, recorded_at, audio_path),
            )
            row = cur.fetchone()
    return _row_to_recording(row)


def update_recording_status(
    recording_id: int, status: str, transcript_path: str | None = None, error: str | None = None
) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f'UPDATE "BW_recordings" SET status = %s, transcript_path = COALESCE(%s, transcript_path), '
                "error = %s, updated_at = now() WHERE id = %s RETURNING {cols}".format(cols=_RECORDING_COLUMNS),
                (status, transcript_path, error, recording_id),
            )
            row = cur.fetchone()
    return _row_to_recording(row) if row else None


def list_recordings(user_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT {_RECORDING_COLUMNS} FROM "BW_recordings" WHERE user_id = %s ORDER BY created_at DESC',
                (user_id,),
            )
            rows = cur.fetchall()
    return [_row_to_recording(row) for row in rows]


def get_recording(recording_id: int, user_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT {_RECORDING_COLUMNS} FROM "BW_recordings" WHERE id = %s AND user_id = %s',
                (recording_id, user_id),
            )
            row = cur.fetchone()
    return _row_to_recording(row) if row else None
