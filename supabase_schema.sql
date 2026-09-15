-- Run this once in the Supabase SQL editor (Project > SQL Editor) if you'd
-- rather create the tables yourself. The backend also creates these
-- automatically on startup once SUPABASE_DB_PASSWORD is set in backend/.env,
-- so running this manually is optional.
--
-- Only metadata lives here — audio files and transcript text are stored on
-- disk (see backend/app/files.py), never in these tables.

CREATE TABLE IF NOT EXISTS "BW_users" (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "BW_recordings" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "BW_users"(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    title TEXT NOT NULL,
    recorded_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'uploaded',
    audio_path TEXT NOT NULL,
    transcript_path TEXT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
