from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from ..config import (
    SUPABASE_DB_HOST,
    SUPABASE_DB_NAME,
    SUPABASE_DB_PASSWORD,
    SUPABASE_DB_PORT,
    SUPABASE_DB_USER,
)

logger = logging.getLogger(__name__)

_schema_ready = False


def is_configured() -> bool:
    return bool(SUPABASE_DB_PASSWORD)


@contextmanager
def get_connection() -> Iterator["psycopg2.extensions.connection"]:  # type: ignore[name-defined]
    import psycopg2  # imported lazily so the package is optional until Supabase is configured

    conn = psycopg2.connect(
        host=SUPABASE_DB_HOST,
        port=SUPABASE_DB_PORT,
        dbname=SUPABASE_DB_NAME,
        user=SUPABASE_DB_USER,
        password=SUPABASE_DB_PASSWORD,
        connect_timeout=10,
        sslmode="require",
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# BW_ prefix on every table, per project naming convention (Book Writing).
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS "BW_users" (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "BW_recordings" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "BW_users"(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    title TEXT NOT NULL,
    recorded_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'uploaded',
    audio_path TEXT NOT NULL,
    transcript_path TEXT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def ensure_schema() -> None:
    """Creates the BW_ tables if they don't exist yet. No-op if Supabase isn't configured."""
    global _schema_ready
    if _schema_ready or not is_configured():
        return
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
    _schema_ready = True
    logger.info("Supabase schema ready (BW_users, BW_recordings)")
