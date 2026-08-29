from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "bookwriting.db"
UPLOAD_DIR = Path(os.getenv("UPLOAD_WORK_DIR", str(DATA_DIR / "uploads")))
if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = BACKEND_DIR / UPLOAD_DIR

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(ROOT_DIR / "voiceoutput")))
if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = BACKEND_DIR / OUTPUT_DIR

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "demo")
TRANSCRIPTION_LANGUAGE_HINT = os.getenv("TRANSCRIPTION_LANGUAGE_HINT", "en-IN")
TRANSCRIPTION_PROMPT_HINT = os.getenv(
    "TRANSCRIPTION_PROMPT_HINT",
    "Indian English travel author documenting a trip around the world.",
)


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
