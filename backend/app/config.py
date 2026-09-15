from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "insecure-dev-secret-change-me")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 12)))
TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "faster-whisper")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
TRANSCRIPTION_LANGUAGE_HINT = os.getenv("TRANSCRIPTION_LANGUAGE_HINT", "en-IN")
TRANSCRIPTION_PROMPT_HINT = os.getenv(
    "TRANSCRIPTION_PROMPT_HINT",
    "Indian English travel author documenting a trip around the world.",
)

# Supabase Postgres (metadata only — audio bytes and transcript text are never
# written to these tables, only file paths). Password is left blank until the
# real one is added to backend/.env; the app falls back to local JSON storage
# until then, so it keeps working end-to-end without Supabase configured.
SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST", "db.hlgipoxusvdymaobxarn.supabase.co")
SUPABASE_DB_PORT = int(os.getenv("SUPABASE_DB_PORT", "5432"))
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER", "postgres")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hlgipoxusvdymaobxarn.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Local file storage roots for audio + transcript files (never stored in the DB).
DATA_DIR = BACKEND_DIR / "data"
AUDIO_STORAGE_DIR = Path(os.getenv("AUDIO_STORAGE_DIR", str(DATA_DIR / "uploads")))
TRANSCRIPT_STORAGE_DIR = Path(os.getenv("TRANSCRIPT_STORAGE_DIR", str(DATA_DIR / "transcripts")))

