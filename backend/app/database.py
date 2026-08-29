from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

from .auth import hash_password
from .config import ADMIN_PASSWORD, ADMIN_USERNAME, DB_PATH, ensure_directories


def get_connection() -> sqlite3.Connection:
    ensure_directories()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def execute(query: str, params: Sequence[object] = ()) -> sqlite3.Cursor:
    with get_connection() as connection:
        cursor = connection.execute(query, params)
        connection.commit()
        return cursor


def executemany(query: str, params: Iterable[Sequence[object]]) -> None:
    with get_connection() as connection:
        connection.executemany(query, params)
        connection.commit()


def fetch_one(query: str, params: Sequence[object] = ()) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(query, params).fetchone()


def fetch_all(query: str, params: Sequence[object] = ()) -> list[sqlite3.Row]:
    with get_connection() as connection:
        return list(connection.execute(query, params).fetchall())


def init_db() -> None:
    ensure_directories()
    schema_path = Path(__file__).with_name("schema.sql")
    with get_connection() as connection:
        connection.executescript(schema_path.read_text())
        existing = connection.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)).fetchone()
        if not existing:
            connection.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD), "admin"),
            )
        connection.commit()
