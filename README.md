# Travel Voice Studio

Travel Voice Studio is a local-first web application for turning travel voice notes into raw transcripts, cleaned transcripts, blog drafts, chapter drafts, summaries, and printable manuscript output.

The current implementation supports an end-to-end demo workflow with the sample MP3 in `SampleVoice/`. Because no live speech-to-text credentials or local Whisper tooling are configured yet, the backend uses `TRANSCRIPTION_PROVIDER=demo` by default so the full app can be tested immediately.

## Run Locally

Start the backend:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Start the frontend:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5175
```

Open:

```text
http://127.0.0.1:5175/
```

Local test login:

```text
admin / admin123
```

## Deploy Frontend to Vercel

This repository keeps the Vite app in `frontend/`, so the root `vercel.json` tells Vercel to install and build from that folder:

```text
npm ci --prefix frontend
npm --prefix frontend run build
```

Vercel publishes `frontend/dist`.

For local development, the frontend calls `/api` and Vite proxies requests to the backend on `127.0.0.1:8765`. For a deployed Vercel frontend, set this environment variable to the deployed backend URL:

```text
VITE_API_BASE_URL=https://your-backend.example.com
```

## Current Workflow

1. Log in.
2. Create or use a travel book trip.
3. Upload one or more audio files.
4. Reorder files by route order.
5. Add country, city, place, date, blog title, and chapter title metadata.
6. Process the batch.
7. Review raw transcript, cleaned transcript, blog draft, and chapter draft.
8. Generate a travel summary.
9. Export output artifacts under `voiceoutput/`.

## Validation

The app has been tested with:

- Backend unit tests: `4 passed`.
- Frontend production build: successful.
- Backend health check: `{"status":"healthy"}`.
- End-to-end sample MP3 flow: login, upload, metadata update, process, summarize, and export succeeded.
