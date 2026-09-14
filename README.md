# BookWriting Travel Studio

BookWriting Travel Studio is a local-first web application for turning travel voice notes into raw transcripts, cleaned transcripts, blog drafts, chapter drafts, summaries, and printable manuscript output.

**No database.** Nothing is persisted on the server: uploads are transcribed in memory/temp storage and the results are returned directly to the browser, which holds all trip/section state for the session. Login uses static credentials from `.env` (no user table). Use **Export** to download the manuscript files before closing the tab.

Transcription runs locally using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (no API key needed). The Whisper `small` model (~250 MB) is downloaded automatically on first use for better accuracy on longer recordings.

## Quick Start (Windows)

After cloning, run the one-time setup script from the repo root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

This will:
- Copy `backend/.env.example` → `backend/.env`
- Install Python dependencies
- Pre-download the Whisper `small` model
- Install frontend Node.js dependencies

Then start both servers (two terminals):

```powershell
# Terminal 1 — backend
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
cd frontend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
npm run dev
```

Open **http://127.0.0.1:5175** and log in with `admin` / `admin123`.

## Workflow

1. Log in (static credentials from `backend/.env`).
2. Set up a trip (kept in the browser only).
3. Upload one or more audio files.
4. Reorder files by route order and add country, city, place, date, blog title, and chapter title metadata.
5. Process the batch (transcription runs locally via Whisper, one file at a time).
6. Review raw transcript, cleaned transcript, blog draft, and chapter draft — edits live in the browser only.
7. Generate a travel summary.
8. Export and download the manuscript files (metadata, transcripts, drafts, printable HTML) — nothing is saved server-side, so download before closing the tab.

## Deployment (Vercel)

`vercel.json` and `api/index.py` at the repo root wire up a combined deployment: the frontend builds as a static site and `/api/*` routes to the FastAPI backend as a Python serverless function. Set `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `APP_SECRET_KEY`, `TRANSCRIPTION_PROVIDER`, and `WHISPER_MODEL` as Vercel environment variables.

**Caveat:** `faster-whisper` (plus its `ctranslate2`/model-weight footprint) is heavy for serverless — it can exceed Vercel's function size limits and its execution-time limits on longer recordings. If deployment fails or times out, host the backend separately (Render, Fly.io, Railway, a VM) and deploy only the frontend to Vercel, or swap in a hosted speech-to-text API in `transcription/provider.py`.

## Validation

The app has been tested with:

## Validation

The app has been tested with:

- Backend unit tests: `4 passed`.
- Frontend production build: successful.
- Backend health check: `{"status":"healthy"}`.
- End-to-end sample MP3 flow: login, upload, metadata update, process, summarize, and export succeeded.
