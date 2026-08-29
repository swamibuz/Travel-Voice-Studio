# BookWriting Travel Studio

BookWriting Travel Studio is a local-first web application for turning travel voice notes into raw transcripts, cleaned transcripts, blog drafts, chapter drafts, summaries, and printable manuscript output.

Transcription runs locally using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (no API key needed). The Whisper `tiny` model (~75 MB) is downloaded automatically on first use.

## Quick Start (Windows)

After cloning, run the one-time setup script from the repo root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

This will:
- Copy `backend/.env.example` → `backend/.env`
- Install Python dependencies
- Pre-download the Whisper `tiny` model
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

1. Log in.
2. Create or use a travel book trip.
3. Upload one or more audio files.
4. Reorder files by route order.
5. Add country, city, place, date, blog title, and chapter title metadata.
6. Process the batch (transcription runs locally via Whisper).
7. Review raw transcript, cleaned transcript, blog draft, and chapter draft.
8. Generate a travel summary.
9. Export output artifacts under `voiceoutput/`.

## Validation

The app has been tested with:

## Validation

The app has been tested with:

- Backend unit tests: `4 passed`.
- Frontend production build: successful.
- Backend health check: `{"status":"healthy"}`.
- End-to-end sample MP3 flow: login, upload, metadata update, process, summarize, and export succeeded.
