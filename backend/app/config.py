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
TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "demo")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
TRANSCRIPTION_LANGUAGE_HINT = os.getenv("TRANSCRIPTION_LANGUAGE_HINT", "en-IN")
TRANSCRIPTION_PROMPT_HINT = os.getenv(
    "TRANSCRIPTION_PROMPT_HINT",
    "Indian English travel author documenting a trip around the world.",
)

