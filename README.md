# Travel Voice Studio

Travel Voice Studio turns travel voice recordings into text. Log in, upload a
recording, click "Convert to Text", and review the transcript — formatted with
the recording title, recorded date/time, and `(m:ss)` timestamped paragraphs.

Transcription runs locally using [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
(no API key or cost). Recording/user metadata is stored in Supabase Postgres
(`BW_users`, `BW_recordings` — see [supabase_schema.sql](supabase_schema.sql)).
Audio files and transcript text are stored on disk, never in the database.
Until `backend/.env` has a real `SUPABASE_DB_PASSWORD`, the app falls back to
a local JSON store so it still works end-to-end without Supabase configured.

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

Also install [ffmpeg](https://ffmpeg.org/) and make sure it's on `PATH` —
faster-whisper uses it to decode audio correctly; without it, some recordings
(especially from phone voice-recorder apps) can get truncated.

Then start both servers (two terminals):

```powershell
# Terminal 1 — backend
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open **http://127.0.0.1:5175** and log in with `admin` / `admin123`.

## Workflow

1. Log in.
2. Upload a voice recording — the Upload button disables once uploaded.
3. Click "Convert to Text" — it shows a processing state until done.
4. Review the formatted transcript, or pick any past recording from the list.

## Deploy Frontend to Vercel

This repository keeps the Vite app in `frontend/`, so the root `vercel.json` tells Vercel to install and build from that folder:

```text
npm ci --prefix frontend
npm --prefix frontend run build
```

Vercel publishes `frontend/dist`.

For local development, the frontend calls `/api` and Vite proxies requests to the backend on `127.0.0.1:8000`. For a deployed Vercel frontend, set this environment variable to the deployed backend URL:

```text
VITE_API_BASE_URL=https://your-backend.example.com
```

**Note:** the FastAPI backend uses `faster-whisper`, which needs a persistent process and isn't a good fit for Vercel serverless functions (package size/timeout limits, and no persistent disk for uploaded audio). Deploy the backend separately (e.g. Render, Railway, Fly.io, or your own VM) and point `VITE_API_BASE_URL` at it.

## Validation

- Backend unit tests: `7 passed`.
- Frontend production build: successful.
- Backend health check: `{"status":"healthy"}`.
- End-to-end flow verified: login, upload, convert, full-length transcript display.

