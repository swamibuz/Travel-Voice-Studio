# Implementation Plan

## 1. Recommended Architecture

Build the application as a local-first travel writing web app with a small backend processing service. The first implementation should help a traveler-author turn voice notes from a trip around the world into visit documentation, blog drafts, chapter drafts, and a combined book manuscript.

- Frontend: React with Vite for upload, ordering, travel metadata, review, editing, summary, and export screens.
- Backend: Python FastAPI for authentication, uploads, job orchestration, transcription, travel metadata extraction, cleanup, summarization, and output file management.
- Storage: local filesystem for audio and generated outputs, with SQLite for metadata and job state.
- Processing: a background worker queue that handles one audio file at a time per batch.
- Output: timestamped run folders under `voiceoutput/`.

This keeps the first version simple, portable, and suitable for local authoring while leaving a clear path to cloud deployment.

## 2. Folder Structure

```text
BookWriting/
  SampleVoice/
    AUDIO-2026-08-29-18-28-45_0506.mp3
  voiceoutput/
  backend/
    app/
      main.py
      auth.py
      config.py
      database.py
      models.py
      schemas.py
      jobs.py
      travel.py
      transcription/
      cleanup/
      summary/
      export/
    tests/
    requirements.txt
    .env.example
  frontend/
    src/
    package.json
  SRS.md
  IMPLEMENTATION_PLAN.md
  SETUP.md
```

## 3. Backend Components

### 3.1 API Layer

- `POST /auth/login` authenticates a user.
- `POST /auth/logout` clears session or token state.
- `POST /uploads` accepts one or more audio files.
- `PATCH /uploads/order` stores user-defined file ordering.
- `PATCH /uploads/{audio_file_id}/travel-metadata` saves trip, country, city, place, visit date, route order, and draft title metadata.
- `POST /jobs` starts sequential processing.
- `GET /jobs/{job_id}` returns batch and per-file status.
- `GET /transcripts/{section_id}` returns raw and cleaned transcript versions.
- `PATCH /transcripts/{section_id}` saves user edits.
- `POST /summaries` creates summaries from selected transcript content.
- `POST /exports/blog` creates blog-post draft output.
- `POST /exports/chapter` creates book-chapter draft output.
- `POST /exports/pdf` creates a PDF-ready manuscript export.
- `GET /outputs/{run_id}` lists generated artifacts.

### 3.2 Data Model

- User: id, username, password hash, role, timestamps.
- Trip: id, owner, title, description, start_date, end_date, route_summary, timestamps.
- UploadBatch: id, owner, status, created_at, completed_at.
- AudioFile: id, batch_id, trip_id, original_name, stored_path, order_index, inferred_title, status, error.
- TravelVisit: id, audio_file_id, trip_id, country, city, place_name, visit_date, route_order, blog_title, chapter_title, tags, notes.
- TranscriptSection: id, audio_file_id, travel_visit_id, raw_text, cleaned_text, blog_draft_text, chapter_draft_text, reviewed_status, timestamps.
- Summary: id, batch_id, trip_id, summary_type, text, created_at.
- OutputArtifact: id, batch_id, artifact_type, path, created_at.

### 3.3 Processing Workflow

1. User logs in.
2. User uploads one or more audio files.
3. Backend stores source files in a timestamped working directory.
4. Frontend displays files and lets the user reorder them.
5. User starts processing.
6. Worker transcribes files sequentially.
7. Worker stores Raw Transcript for each file.
8. Worker extracts or suggests travel metadata such as country, city, place, visit date, route order, blog title, and chapter title.
9. Worker creates Cleaned English Transcript for each file.
10. Worker creates optional blog-post and chapter-draft versions from the cleaned transcript.
11. Backend combines approved or selected sections by route order, country, city, or user-defined chapter order.
12. User reviews and edits travel metadata and cleaned text.
13. User generates summaries such as itinerary overview, key experiences, recommendations, and lessons learned.
14. User exports blog drafts, chapter drafts, or print/PDF-ready manuscript output.
15. Backend writes final artifacts into `voiceoutput/<timestamp>/`.

## 4. Transcription Strategy

Implement a provider interface first:

```text
TranscriptionProvider
  transcribe(audio_path, language_hint, prompt_hint) -> TranscriptResult
```

Recommended providers:

- Azure AI Speech for production-grade enterprise deployment and regional control.
- OpenAI transcription APIs for strong general transcription quality and simple API integration.
- faster-whisper for offline/local transcription when privacy or connectivity is the priority.

Initial configuration should support one active provider through environment variables.

## 5. Travel Writing and Indian English Handling

- Use `en-IN` or equivalent language hints where the provider supports it.
- Allow a custom vocabulary prompt containing names, countries, cities, landmarks, local food names, cultural terms, book-specific terms, and common Indian English expressions.
- Keep the raw transcript immutable by default.
- Use cleanup prompts that explicitly say: improve grammar and punctuation without omitting content, changing meaning, or replacing Indian English expressions unnecessarily.
- Use travel-writing prompts that preserve first-person experience, chronology, location details, observations, feelings, and practical notes.
- Ask the model to flag uncertain place names rather than inventing or over-correcting them.
- Keep blog and chapter generation separate from raw transcription so the user can compare the source voice note with the edited travel narrative.

## 6. Cleanup and Summarization

Use a text model through a small provider abstraction:

```text
TextGenerationProvider
  clean(raw_text, style_rules) -> cleaned_text
  create_blog_draft(cleaned_text, travel_metadata, style_rules) -> blog_draft_text
  create_chapter_draft(cleaned_text, travel_metadata, style_rules) -> chapter_draft_text
  summarize(cleaned_text, length, scope) -> summary_text
```

Cleanup rules:

- Preserve meaning.
- Do not remove uncertain phrases.
- Keep names and local terminology.
- Preserve travel chronology, places visited, route details, cultural observations, costs, recommendations, and personal reflections.
- Add paragraph breaks for readability.
- Mark unclear words as `[unclear]` only when necessary.

Blog draft rules:

- Start from the cleaned transcript, not directly from the raw transcript.
- Organize one visit into a readable blog post with a title, introduction, body sections, and closing reflection.
- Preserve first-person voice and avoid adding unsupported facts.
- Keep uncertain facts visibly marked for user review.

Chapter draft rules:

- Use a more book-like narrative flow than the blog draft.
- Support chapter titles, subtitles, and section breaks.
- Preserve the author's personal voice and route chronology.
- Avoid turning the chapter into generic travel marketing copy.

Summary rules:

- Summarize only from the transcript, not outside knowledge.
- Support chapter-wise and full-document summaries.
- Support travel-specific summaries: itinerary, places visited, memorable moments, recommendations, and lessons learned.
- Keep summary separate from source transcript.

## 7. Frontend Screens

- Login screen.
- Trip dashboard with current trip, route, countries, cities, and processing runs.
- Upload screen with drag-and-drop file selection.
- Ordering screen with drag-and-drop sorting.
- Processing screen with batch and file status.
- Travel metadata screen for country, city, place, date, route order, blog title, and chapter title.
- Review screen with Raw Transcript and Cleaned Transcript views.
- Blog draft screen for visit-level publishing drafts.
- Chapter draft screen for book manuscript drafts.
- Combined transcript screen.
- Summary screen.
- Export screen with print and PDF options.
- Settings screen for provider, language hint, vocabulary prompt, and retention policy.

## 8. PDF and Print

Use HTML print styles for the first version. Add server-side PDF generation after the transcript workflow is stable.

Recommended options:

- Browser print for fast initial delivery.
- Playwright or WeasyPrint for backend-generated PDFs.

## 9. Security Plan

- Use hashed passwords with `passlib` or equivalent.
- Store sessions in secure HTTP-only cookies for local web use.
- Store provider keys only in `.env`, never in source control.
- Add `.gitignore` entries for `.env`, uploaded working files, local databases, and generated outputs if this becomes a Git repo.
- Log request IDs, job IDs, and statuses, but not secrets or full credentials.

## 10. Testing Plan

- Unit tests for filename section inference.
- Unit tests for travel metadata inference from filenames and transcript snippets.
- Unit tests for provider abstractions using mocked transcription responses.
- Unit tests for transcript cleanup rules.
- Unit tests for blog draft and chapter draft generation prompts using mocked text model responses.
- API tests for upload, ordering, job status, transcript retrieval, and export creation.
- End-to-end test for one sample MP3 from upload through output artifact creation.
- Manual review test for Indian English accuracy using the sample voice file once transcription credentials or a local model are available.
- Manual review test that confirms travel place names, route order, and first-person narration are preserved.

## 11. Milestones

### Milestone 1: Documentation and Skeleton

- Finalize SRS, implementation plan, and setup guide.
- Create backend and frontend skeletons.
- Add `.env.example` and `.gitignore`.

### Milestone 2: Upload and Ordering

- Implement login.
- Implement single and multi-file upload.
- Implement drag-and-drop ordering.
- Implement trip and travel visit metadata forms.
- Store metadata in SQLite.

### Milestone 3: Transcription Pipeline

- Add transcription provider abstraction.
- Implement one provider.
- Add sequential processing and status tracking.
- Write raw transcripts to the database and `voiceoutput/`.

### Milestone 4: Cleanup, Review, and Combine

- Add cleaned transcript generation with travel-aware cleanup rules.
- Add review/edit UI.
- Add combined transcript generation.
- Add blog-post and chapter-draft generation.

### Milestone 5: Summary and Export

- Add travel-aware summarization.
- Add print view.
- Add blog, chapter, and PDF-ready manuscript export.
- Add timestamped output folders.

### Milestone 6: Hardening

- Add retries, retention controls, structured logs, and tests.
- Validate accuracy with the sample voice file.

## 12. Immediate Next Build Step

Create the FastAPI backend skeleton and React frontend skeleton, then implement trip setup, upload, ordering, and travel metadata editing before integrating a transcription provider.