from __future__ import annotations

import hmac
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .auth import create_session_token, verify_session_token
from .cleanup.service import clean_transcript, create_blog_draft, create_chapter_draft
from .config import ADMIN_PASSWORD, ADMIN_USERNAME, APP_SECRET_KEY, SESSION_TTL_SECONDS
from .export.service import build_markdown, build_metadata_json, build_printable_html
from .models import ExportRequest, InferMetadataRequest, LoginRequest, SummaryRequest
from .summary.service import summarize_sections
from .transcription.provider import transcribe_audio
from .travel import display_location, infer_metadata

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


def require_user(authorization: str = Header(default="")) -> dict[str, object]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    session = verify_session_token(token, APP_SECRET_KEY)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    return session


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/auth/login")
def login(request: LoginRequest) -> dict[str, object]:
    # Static credentials from .env — no database, works on stateless deployments (e.g. Vercel).
    valid = hmac.compare_digest(request.username, ADMIN_USERNAME) and hmac.compare_digest(request.password, ADMIN_PASSWORD)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_session_token(ADMIN_USERNAME, "admin", APP_SECRET_KEY, SESSION_TTL_SECONDS)
    return {"token": token, "user": {"username": ADMIN_USERNAME, "role": "admin"}}


@app.post("/auth/logout")
def logout(authorization: str = Header(default="")) -> dict[str, str]:
    # Tokens are stateless and self-expiring; the client simply discards it.
    return {"status": "logged_out"}


@app.post("/metadata/infer")
def infer_metadata_batch(request: InferMetadataRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    items = [{"filename": item.filename, **infer_metadata(item.filename, item.order_index)} for item in request.files]
    return {"items": items}


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    original_name: str = Form(""),
    country: str = Form(""),
    city: str = Form(""),
    place_name: str = Form(""),
    visit_date: str = Form(""),
    blog_title: str = Form(""),
    chapter_title: str = Form(""),
    user: dict[str, object] = Depends(require_user),
) -> dict[str, object]:
    # No database and no persistent disk storage — the audio only exists for the
    # duration of this request, in a temp file, then the client keeps the results.
    name = original_name or file.filename or "voice-note"
    metadata = {"country": country, "city": city, "place_name": place_name, "visit_date": visit_date}
    suffix = Path(name).suffix or ".mp3"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(await file.read())
        tmp_path = handle.name

    try:
        raw_text = transcribe_audio(tmp_path, name, metadata)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Transcription failed: {exc}") from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    location = display_location(metadata)
    cleaned_text = clean_transcript(raw_text)
    blog_draft = create_blog_draft(cleaned_text, blog_title, location)
    chapter_draft = create_chapter_draft(cleaned_text, chapter_title, location)
    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "blog_draft_text": blog_draft,
        "chapter_draft_text": chapter_draft,
        "location": location,
    }


@app.post("/summaries")
def create_summary(request: SummaryRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    sections = [dict(section) for section in request.sections]
    for section in sections:
        section.setdefault("location", display_location(section))
    text = summarize_sections(sections, request.summary_type)
    return {"text": text}


@app.post("/exports")
def export_batch(request: ExportRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    sections = [dict(section) for section in request.sections]
    if not sections:
        raise HTTPException(status_code=404, detail="No sections to export")
    for section in sections:
        section.setdefault("location", display_location(section))

    files = {
        "metadata.json": build_metadata_json(sections),
        "raw_transcript.md": build_markdown("Raw Travel Voice Transcript", sections, "raw_text"),
        "cleaned_transcript.md": build_markdown("Cleaned Travel Transcript", sections, "cleaned_text"),
        "blog_drafts.md": build_markdown("Travel Blog Drafts", sections, "blog_draft_text"),
        "chapter_drafts.md": build_markdown("Travel Book Chapter Drafts", sections, "chapter_draft_text"),
        "printable.html": build_printable_html(request.title, sections, request.include_raw),
    }
    return {"files": files}
