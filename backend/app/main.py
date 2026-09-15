from __future__ import annotations

import hmac
import re
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import repository
from .auth import create_session_token, verify_password, verify_session_token
from .config import APP_SECRET_KEY, SESSION_TTL_SECONDS
from .files import read_transcript, save_audio, save_transcript
from .models import LoginRequest
from .transcription.format import format_transcript
from .transcription.provider import transcribe_audio_segments

app = FastAPI(title="BookWriting Travel Voice API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    repository.init()


def require_user(authorization: str = Header(default="")) -> dict[str, object]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    session = verify_session_token(token, APP_SECRET_KEY)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    return session


def recording_title(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = re.sub(r"[_-]+", " ", stem)
    return re.sub(r"\s+", " ", cleaned).strip() or "Voice Recording"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/auth/login")
def login(request: LoginRequest) -> dict[str, object]:
    user = repository.get_user_by_username(request.username)
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_session_token(user["username"], "user", APP_SECRET_KEY, SESSION_TTL_SECONDS)
    return {"token": token, "user": {"username": user["username"]}}


@app.post("/auth/logout")
def logout(authorization: str = Header(default="")) -> dict[str, str]:
    # Tokens are stateless and self-expiring; the client simply discards it.
    return {"status": "logged_out"}


def _recording_summary(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": row["id"],
        "title": row["title"],
        "recorded_at": row["recorded_at"],
        "status": row["status"],
        "error": row["error"],
    }


@app.get("/recordings")
def get_recordings(user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    user_row = repository.get_user_by_username(str(user["username"]))
    if not user_row:
        raise HTTPException(status_code=401, detail="Unknown user")
    rows = repository.list_recordings(int(user_row["id"]))
    return {"items": [_recording_summary(row) for row in rows]}


@app.post("/recordings")
async def upload_recording(
    file: UploadFile = File(...),
    original_name: str = Form(""),
    recorded_at: str = Form(""),
    user: dict[str, object] = Depends(require_user),
) -> dict[str, object]:
    user_row = repository.get_user_by_username(str(user["username"]))
    if not user_row:
        raise HTTPException(status_code=401, detail="Unknown user")

    name = original_name or file.filename or "voice-note"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")

    audio_path = save_audio(int(user_row["id"]), name, content)
    row = repository.create_recording(
        user_id=int(user_row["id"]),
        original_filename=name,
        title=recording_title(name),
        recorded_at=recorded_at or None,
        audio_path=audio_path,
    )
    return _recording_summary(row)


@app.post("/recordings/{recording_id}/convert")
def convert_recording(recording_id: int, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    user_row = repository.get_user_by_username(str(user["username"]))
    if not user_row:
        raise HTTPException(status_code=401, detail="Unknown user")

    row = repository.get_recording(recording_id, int(user_row["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="Recording not found")

    repository.update_recording_status(recording_id, "processing")
    try:
        segments = transcribe_audio_segments(row["audio_path"])
        transcript = format_transcript(row["title"], row["recorded_at"], segments)
    except Exception as exc:
        repository.update_recording_status(recording_id, "failed", error=str(exc))
        raise HTTPException(status_code=422, detail=f"Transcription failed: {exc}") from exc

    transcript_path = save_transcript(int(user_row["id"]), recording_id, transcript)
    updated = repository.update_recording_status(recording_id, "completed", transcript_path=transcript_path)
    return {**_recording_summary(updated), "transcript": transcript}


@app.get("/recordings/{recording_id}")
def get_recording_detail(recording_id: int, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    user_row = repository.get_user_by_username(str(user["username"]))
    if not user_row:
        raise HTTPException(status_code=401, detail="Unknown user")

    row = repository.get_recording(recording_id, int(user_row["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="Recording not found")

    transcript = read_transcript(row["transcript_path"]) if row["transcript_path"] else ""
    return {**_recording_summary(row), "transcript": transcript}

