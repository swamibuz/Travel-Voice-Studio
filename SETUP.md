# Setup Guide

## 1. Prerequisites

- macOS, Linux, or Windows with a Unix-like shell.
- Python 3.11 or newer.
- Node.js 20 or newer.
- A speech-to-text provider account or a local Whisper-compatible setup.
- Optional but recommended: `ffmpeg` for audio inspection and conversion.

On macOS, install optional audio tooling with Homebrew:

```bash
brew install ffmpeg
```

## 2. Current Workspace

The workspace currently contains:

```text
SampleVoice/
  AUDIO-2026-08-29-18-28-45_0506.mp3
voiceoutput/
```

The sample file was detected as MP3 audio. Live transcription has not been run yet because this machine currently does not have `ffmpeg`, `ffprobe`, Whisper CLI, faster-whisper, or speech provider credentials configured. The implemented app therefore defaults to `TRANSCRIPTION_PROVIDER=demo` so the upload, ordering, metadata, processing, review, summary, and export workflow can be tested end to end.

## 3. Recommended Environment Variables

Create a `.env` file in the backend folder when the application skeleton exists.

```bash
APP_ENV=local
APP_SECRET_KEY=change-this-local-secret

ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password

TRANSCRIPTION_PROVIDER=faster-whisper
WHISPER_MODEL=small
TRANSCRIPTION_LANGUAGE_HINT=en-IN
TRANSCRIPTION_PROMPT_HINT=Indian English speaker. Preserve names, places, Indian English phrasing, and book-specific terminology.
```

There is no database and no server-side file storage — uploads are transcribed in a temp file per request and the results are returned directly to the browser, which holds all state for the session.

## 4. Backend Setup

After the backend skeleton is created:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pytest
cp .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

Expected local backend URL:

```text
http://localhost:8765
```

Expected API documentation URL:

```text
http://localhost:8765/docs
```

## 5. Frontend Setup

After the frontend skeleton is created:

```bash
cd frontend
npm install
npm run dev
```

Expected local frontend URL:

```text
http://localhost:5175
```

## 6. Transcription Provider Options

### Option A: Demo Transcription

Set:

```bash
TRANSCRIPTION_PROVIDER=demo
```

This mode creates deterministic demo transcript text from the uploaded audio filename and travel metadata. Use it for local end-to-end testing before configuring real speech-to-text.

### Option B: OpenAI Transcription

Set:

```bash
TRANSCRIPTION_PROVIDER=openai
OPENAI_API_KEY=your-api-key
TRANSCRIPTION_LANGUAGE_HINT=en-IN
```

The application should send the audio file with a prompt hint for Indian English and domain vocabulary.

### Option C: Azure AI Speech

Set:

```bash
TRANSCRIPTION_PROVIDER=azure-speech
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=your-region
TRANSCRIPTION_LANGUAGE_HINT=en-IN
```

Azure AI Speech is a strong option when you want Azure-native operations, enterprise controls, and regional deployment.

### Option D: Local Whisper or faster-whisper

Install local tooling in the backend virtual environment:

```bash
python -m pip install faster-whisper
brew install ffmpeg
```

Set:

```bash
TRANSCRIPTION_PROVIDER=faster-whisper
WHISPER_MODEL=small
TRANSCRIPTION_LANGUAGE_HINT=en
```

Choose a model size based on local machine performance. Larger models are slower but usually more accurate.

## 7. Processing the Sample Audio

Once the app skeleton and transcription provider are configured, use this sample file for the first end-to-end test:

```text
SampleVoice/AUDIO-2026-08-29-18-28-45_0506.mp3
```

Expected result:

- A raw transcript is created.
- A cleaned English transcript is created.
- A blog draft and chapter draft are created.
- A summary can be generated.
- Export returns downloadable files directly to the browser (nothing is written to disk on the server).

## 8. Output Files

Export produces these files, downloaded straight to the browser:

```text
metadata.json
raw_transcript.md
cleaned_transcript.md
blog_drafts.md
chapter_drafts.md
printable.html
```

Download them before closing the tab — the app does not keep a copy after the response is sent.

## 9. Local Development Checks

Backend checks:

```bash
cd backend
source .venv/bin/activate
python -m pytest
python -m ruff check .
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

These commands apply after the backend and frontend projects are created and their dependencies are installed.

## 10. Deployment Notes

For a simple first deployment, use:

- Frontend: Azure Static Web Apps, Vercel, Netlify, or any static host.
- Backend: Azure App Service, Azure Container Apps, or a VM/container host.
- Storage: local disk for single-machine deployment, Azure Blob Storage for cloud deployment.
- Database: SQLite for local use, PostgreSQL for multi-user cloud use.

For cloud deployment, move source audio and output artifacts to durable object storage instead of relying only on container-local disk.

## 11. Troubleshooting

### No transcription is produced

- Confirm `TRANSCRIPTION_PROVIDER` is set.
- Confirm the selected provider credentials are present.
- Confirm `ffmpeg` is installed if the provider or local model needs audio conversion.
- Check job status and backend logs.

### Indian English words are rewritten incorrectly

- Add recurring names, places, and phrases to `TRANSCRIPTION_PROMPT_HINT`.
- Review the cleanup prompt and ensure it says not to change meaning or replace Indian English unnecessarily.
- Preserve the raw transcript for comparison.

### Output folder is empty

- Confirm `OUTPUT_DIR` points to `../voiceoutput` or another writable directory.
- Confirm at least one transcript section completed successfully.
- Check export errors in the job status response.

## 12. Security Checklist

- Do not commit `.env`.
- Do not print API keys in logs.
- Use a strong admin password.
- Delete uploaded audio after the retention period if it is no longer needed.
- Keep raw and cleaned transcripts separate so edits do not erase the original record.