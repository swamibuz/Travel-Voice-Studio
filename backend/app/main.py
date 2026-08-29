from __future__ import annotations

import shutil
import secrets
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .auth import hash_password, verify_password
from .cleanup.service import clean_transcript, create_blog_draft, create_chapter_draft
from .config import UPLOAD_DIR, ensure_directories
from .database import execute, fetch_all, fetch_one, init_db
from .export.service import create_run_folder, write_markdown, write_metadata, write_printable_html
from .models import ExportRequest, LoginRequest, OrderRequest, SummaryRequest, TranscriptUpdateRequest, TravelMetadataRequest, TripRequest
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


@app.on_event("startup")
def startup() -> None:
    init_db()


def row_to_dict(row) -> dict[str, object]:
    return dict(row) if row else {}


def require_user(authorization: str = Header(default="")) -> dict[str, object]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    session = fetch_one(
        "SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id WHERE sessions.token = ?",
        (token,),
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    return row_to_dict(session)


def default_trip_id() -> int:
    trip = fetch_one("SELECT id FROM trips ORDER BY id LIMIT 1")
    if trip:
        return int(trip["id"])
    cursor = execute(
        "INSERT INTO trips (title, description) VALUES (?, ?)",
        ("Around the World Travel Book", "Voice notes for travel blogs and a book manuscript."),
    )
    return int(cursor.lastrowid)


def get_sections(batch_id: int) -> list[dict[str, object]]:
    rows = fetch_all(
        """
        SELECT audio_files.*, transcripts.raw_text, transcripts.cleaned_text,
               transcripts.blog_draft_text, transcripts.chapter_draft_text, transcripts.reviewed_status
        FROM audio_files
        LEFT JOIN transcripts ON transcripts.audio_file_id = audio_files.id
        WHERE audio_files.batch_id = ?
        ORDER BY audio_files.route_order, audio_files.order_index, audio_files.id
        """,
        (batch_id,),
    )
    sections = []
    for row in rows:
        section = row_to_dict(row)
        section["location"] = display_location(section)
        sections.append(section)
    return sections


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/auth/login")
def login(request: LoginRequest) -> dict[str, object]:
    user = fetch_one("SELECT * FROM users WHERE username = ?", (request.username,))
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not str(user["password"]).startswith("pbkdf2_sha256$"):
        execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(request.password), user["id"]))
    token = secrets.token_urlsafe(32)
    execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user["id"]))
    return {"token": token, "user": {"username": user["username"], "role": user["role"]}}


@app.post("/auth/logout")
def logout(authorization: str = Header(default="")) -> dict[str, str]:
    token = authorization.removeprefix("Bearer ").strip()
    if token:
        execute("DELETE FROM sessions WHERE token = ?", (token,))
    return {"status": "logged_out"}


@app.get("/trips")
def list_trips(user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    return {"trips": [row_to_dict(row) for row in fetch_all("SELECT * FROM trips ORDER BY id DESC")]}


@app.post("/trips")
def create_trip(request: TripRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    cursor = execute(
        "INSERT INTO trips (title, description, start_date, end_date, route_summary) VALUES (?, ?, ?, ?, ?)",
        (request.title, request.description, request.start_date, request.end_date, request.route_summary),
    )
    return row_to_dict(fetch_one("SELECT * FROM trips WHERE id = ?", (cursor.lastrowid,)))


@app.get("/batches")
def list_batches(user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    return {"batches": [row_to_dict(row) for row in fetch_all("SELECT * FROM batches ORDER BY id DESC")]}


@app.post("/uploads")
async def upload_files(files: list[UploadFile] = File(...), trip_id: Optional[int] = None, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    ensure_directories()
    active_trip_id = trip_id or default_trip_id()
    batch_cursor = execute("INSERT INTO batches (trip_id, status) VALUES (?, ?)", (active_trip_id, "uploaded"))
    batch_id = int(batch_cursor.lastrowid)
    batch_dir = UPLOAD_DIR / f"batch-{batch_id}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []
    for order_index, upload in enumerate(files):
        metadata = infer_metadata(upload.filename, order_index)
        safe_name = Path(upload.filename).name
        stored_path = batch_dir / f"{order_index + 1:03d}-{safe_name}"
        with stored_path.open("wb") as destination:
            shutil.copyfileobj(upload.file, destination)
        cursor = execute(
            """
            INSERT INTO audio_files (
              batch_id, original_name, stored_path, content_type, file_size, order_index,
              inferred_title, visit_date, route_order, blog_title, chapter_title
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                upload.filename,
                str(stored_path),
                upload.content_type or "",
                stored_path.stat().st_size,
                order_index,
                metadata["inferred_title"],
                metadata["visit_date"],
                metadata["route_order"],
                metadata["blog_title"],
                metadata["chapter_title"],
            ),
        )
        uploaded.append(row_to_dict(fetch_one("SELECT * FROM audio_files WHERE id = ?", (cursor.lastrowid,))))
    return {"batch_id": batch_id, "files": uploaded}


@app.patch("/uploads/order")
def update_order(request: OrderRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    for item in request.items:
        execute("UPDATE audio_files SET order_index = ?, route_order = ? WHERE id = ?", (item.order_index, item.order_index + 1, item.id))
    return {"status": "updated"}


@app.patch("/uploads/{audio_file_id}/travel-metadata")
def update_travel_metadata(audio_file_id: int, request: TravelMetadataRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    execute(
        """
        UPDATE audio_files
        SET country = ?, city = ?, place_name = ?, visit_date = ?, route_order = ?,
            blog_title = ?, chapter_title = ?, tags = ?, notes = ?
        WHERE id = ?
        """,
        (
            request.country,
            request.city,
            request.place_name,
            request.visit_date,
            request.route_order,
            request.blog_title,
            request.chapter_title,
            request.tags,
            request.notes,
            audio_file_id,
        ),
    )
    return row_to_dict(fetch_one("SELECT * FROM audio_files WHERE id = ?", (audio_file_id,)))


@app.post("/jobs/{batch_id}/process")
def process_batch(batch_id: int, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    files = fetch_all("SELECT * FROM audio_files WHERE batch_id = ? ORDER BY order_index, id", (batch_id,))
    if not files:
        raise HTTPException(status_code=404, detail="Batch has no files")
    execute("UPDATE batches SET status = ? WHERE id = ?", ("processing", batch_id))
    for row in files:
        file_record = row_to_dict(row)
        try:
            execute("UPDATE audio_files SET status = ?, error = '' WHERE id = ?", ("processing", row["id"]))
            raw_text = transcribe_audio(row["stored_path"], row["original_name"], file_record)
            cleaned_text = clean_transcript(raw_text)
            location = display_location(file_record)
            blog_draft = create_blog_draft(cleaned_text, str(row["blog_title"]), location)
            chapter_draft = create_chapter_draft(cleaned_text, str(row["chapter_title"]), location)
            execute(
                """
                INSERT INTO transcripts (audio_file_id, raw_text, cleaned_text, blog_draft_text, chapter_draft_text)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(audio_file_id) DO UPDATE SET
                  raw_text = excluded.raw_text,
                  cleaned_text = excluded.cleaned_text,
                  blog_draft_text = excluded.blog_draft_text,
                  chapter_draft_text = excluded.chapter_draft_text,
                  updated_at = CURRENT_TIMESTAMP
                """,
                (row["id"], raw_text, cleaned_text, blog_draft, chapter_draft),
            )
            execute("UPDATE audio_files SET status = ? WHERE id = ?", ("complete", row["id"]))
        except Exception as exc:
            execute("UPDATE audio_files SET status = ?, error = ? WHERE id = ?", ("failed", str(exc), row["id"]))
    execute("UPDATE batches SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?", ("complete", batch_id))
    return {"batch_id": batch_id, "sections": get_sections(batch_id)}


@app.get("/jobs/{batch_id}")
def get_job(batch_id: int, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    batch = fetch_one("SELECT * FROM batches WHERE id = ?", (batch_id,))
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"batch": row_to_dict(batch), "sections": get_sections(batch_id)}


@app.patch("/transcripts/{audio_file_id}")
def update_transcript(audio_file_id: int, request: TranscriptUpdateRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    execute(
        """
        UPDATE transcripts
        SET cleaned_text = ?, blog_draft_text = ?, chapter_draft_text = ?, reviewed_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE audio_file_id = ?
        """,
        (request.cleaned_text, request.blog_draft_text, request.chapter_draft_text, request.reviewed_status, audio_file_id),
    )
    return {"status": "updated", "section": get_sections_for_audio(audio_file_id)}


def get_sections_for_audio(audio_file_id: int) -> dict[str, object]:
    row = fetch_one(
        """
        SELECT audio_files.*, transcripts.raw_text, transcripts.cleaned_text,
               transcripts.blog_draft_text, transcripts.chapter_draft_text, transcripts.reviewed_status
        FROM audio_files
        LEFT JOIN transcripts ON transcripts.audio_file_id = audio_files.id
        WHERE audio_files.id = ?
        """,
        (audio_file_id,),
    )
    section = row_to_dict(row)
    section["location"] = display_location(section)
    return section


@app.post("/summaries")
def create_summary(request: SummaryRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    sections = get_sections(request.batch_id)
    text = summarize_sections(sections, request.summary_type)
    cursor = execute(
        "INSERT INTO summaries (batch_id, summary_type, text) VALUES (?, ?, ?)",
        (request.batch_id, request.summary_type, text),
    )
    return {"id": cursor.lastrowid, "text": text}


@app.post("/exports")
def export_batch(request: ExportRequest, user: dict[str, object] = Depends(require_user)) -> dict[str, object]:
    sections = get_sections(request.batch_id)
    if not sections:
        raise HTTPException(status_code=404, detail="Batch has no transcript sections")
    run_dir = create_run_folder(request.batch_id)
    artifacts = {
        "metadata": run_dir / "metadata.json",
        "raw_transcript": run_dir / "raw_transcript.md",
        "cleaned_transcript": run_dir / "cleaned_transcript.md",
        "blog_drafts": run_dir / "blog_drafts.md",
        "chapter_drafts": run_dir / "chapter_drafts.md",
        "printable": run_dir / "printable.html",
    }
    write_metadata(artifacts["metadata"], request.batch_id, sections)
    write_markdown(artifacts["raw_transcript"], "Raw Travel Voice Transcript", sections, "raw_text")
    write_markdown(artifacts["cleaned_transcript"], "Cleaned Travel Transcript", sections, "cleaned_text")
    write_markdown(artifacts["blog_drafts"], "Travel Blog Drafts", sections, "blog_draft_text")
    write_markdown(artifacts["chapter_drafts"], "Travel Book Chapter Drafts", sections, "chapter_draft_text")
    write_printable_html(artifacts["printable"], "Travel Book Manuscript", sections, request.include_raw)
    for artifact_type, path in artifacts.items():
        execute("INSERT INTO output_artifacts (batch_id, artifact_type, path) VALUES (?, ?, ?)", (request.batch_id, artifact_type, str(path)))
    return {"run_dir": str(run_dir), "artifacts": {key: str(path) for key, path in artifacts.items()}}
