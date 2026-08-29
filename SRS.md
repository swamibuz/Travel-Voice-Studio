# Software Requirements Specification

## 1. Product Overview

The BookWriting application converts one or more spoken audio recordings into structured travel writing material for an author documenting a trip around the world. It accepts uploaded audio files from visits, transcribes them sequentially, preserves the original transcript, produces a cleaned English transcript, helps organize each visit into blog-style sections or book chapters, combines sections into one manuscript, supports review and editing, summarizes the material, and exports printable or PDF-ready output.

The workspace currently contains this sample audio file:

- `SampleVoice/AUDIO-2026-08-29-18-28-45_0506.mp3`

The sample file is an MP3 identified as MPEG Layer III audio at 48 kHz and 320 kbps. It has not yet been transcribed in this workspace because no local speech-to-text tool or speech provider credentials are configured.

## 2. Goals

- Convert spoken Indian English audio into accurate English text.
- Support a travel-blog-to-book workflow for documenting countries, cities, places visited, dates, experiences, reflections, and practical travel notes.
- Support Indian accents, common Indian English phrasing, and code-switched or informal spoken expressions where present.
- Preserve a raw transcript before any cleanup or rewriting.
- Produce a cleaned transcript that improves punctuation, grammar, paragraphing, and readability without changing meaning or omitting content.
- Convert cleaned transcripts into travel-friendly writing that can become blog posts, visit notes, chapter drafts, or a full travel memoir manuscript.
- Let the user combine, edit, summarize, print, and export the resulting book material.
- Save generated outputs into `voiceoutput/` using timestamped folders or filenames.

## 3. Users

- Primary user: a traveler-author recording spoken memories, observations, and visit documentation from a trip around the world, then turning those recordings into blog posts and book chapters.
- Secondary user: an editor helping refine travel narratives, location details, chronology, and manuscript structure.
- Admin user: manages authentication, configuration, retention settings, and transcription provider settings.

## 4. Functional Requirements

### 4.1 Authentication

- The system shall provide login and logout.
- The system shall protect upload, transcript, export, and settings pages behind authentication.
- The system shall support password hashing and session or token expiration.
- The system should support a single local admin account for initial local deployment.

### 4.2 Audio Upload

- The system shall allow single audio upload.
- The system shall allow multiple audio uploads in one batch.
- The system shall support common audio formats including MP3, WAV, M4A, AAC, FLAC, OGG, WebM, and MP4 audio.
- The system shall validate file type, file size, and upload completeness.
- The system shall display each uploaded file name, size, status, and processing result.

### 4.3 Drag-and-Drop Ordering

- The system shall allow uploaded files to be reordered before processing.
- The system shall process files according to the user-defined order.
- The system shall preserve the final order in the transcript metadata.

### 4.4 Sequential Transcription

- The system shall transcribe multiple files sequentially by default.
- The system shall show per-file progress: queued, processing, complete, failed, or skipped.
- The system shall continue to the next file when one file fails, while preserving the error state.
- The system shall support retry for failed files.

### 4.5 Filename-Based Section Identification

- The system shall infer section names from filenames when possible.
- The system shall preserve the original filename with each transcript section.
- The system should allow users to edit inferred section titles before final export.
- The system should support filename patterns such as chapter number, date, country, city, place name, topic, or sequence number.
- The system should infer travel metadata when present in filenames, including visit date, location, and stop number.

### 4.6 Travel Visit Documentation

- The system shall support organizing recordings by trip, country, city, location, visit date, and chapter or blog-post sequence.
- The system shall allow users to add or edit travel metadata for each audio section.
- The system shall support both blog-style output for individual visits and book-style output for a combined manuscript.
- The system shall preserve first-person travel voice, personal reflections, and chronological experience unless the user edits them.
- The system should help identify and structure common travel content such as arrival, place visited, people met, food, culture, costs, lessons learned, memorable incidents, recommendations, and closing reflections.
- The system should generate optional titles and subtitles suitable for travel blog posts or chapter headings.

### 4.7 Indian English and Accent Handling

- The transcription workflow shall use an engine or model suitable for Indian English accents.
- The system shall allow prompt or configuration hints for Indian English, speaker style, travel domain terms, names, countries, cities, landmarks, local phrases, and recurring vocabulary.
- The cleaning workflow shall retain Indian English meaning and culturally specific wording unless the user explicitly edits it.
- The system shall not silently replace Indian English terms with unrelated American or British phrasing.
- The system shall avoid incorrectly normalizing location names, food names, cultural references, or local expressions.

### 4.8 Transcript Versions

- The system shall retain a Raw Transcript for each audio file.
- The Raw Transcript shall represent, as closely as possible, the actual spoken words.
- The system shall retain a Cleaned English Transcript for each audio file.
- The Cleaned English Transcript shall improve readability, punctuation, grammar, sentence boundaries, and paragraphing without changing meaning.
- The system shall show both versions side by side or in clearly separated tabs.

### 4.9 Combined Transcript

- The system shall combine all selected transcript sections in the chosen order.
- The combined transcript shall include section headings derived from filenames or user-edited titles.
- The combined transcript shall support grouping sections by trip, country, city, or chronological route.
- The user shall be able to regenerate the combined transcript after edits.

### 4.10 Editing and Review

- The system shall allow users to edit raw transcript text only with an explicit warning or separate correction mode.
- The system shall allow users to freely edit cleaned transcript text.
- The system shall track whether each section is unreviewed, reviewed, or approved.
- The system shall allow users to correct travel metadata such as place names, dates, route order, and chapter titles.
- The system should autosave edits.

### 4.11 Summarization

- The system shall generate a summary from the cleaned combined transcript.
- The summary shall not replace the transcript.
- The system should support short, medium, and detailed summary lengths.
- The system should support chapter-wise summaries and a full-document summary.
- The system should support travel-specific summaries such as itinerary overview, key experiences, places visited, recommendations, and lessons learned.

### 4.12 Print and PDF Output

- The system shall provide a print-friendly view.
- The system shall export PDF-ready content containing selected travel sections, the combined cleaned transcript, optional summaries, and travel metadata when selected.
- The system should allow the user to include or exclude raw transcripts in exported output.
- The system should support separate export formats for blog post drafts, chapter drafts, and full manuscript drafts.

### 4.13 Output Folder and Timestamped Results

- The system shall save generated outputs under `voiceoutput/`.
- The system shall create timestamped output names or folders for each processing run.
- The system shall save metadata with each run, including source filenames, order, status, transcript provider, timestamps, and errors.

### 4.14 Status and Error Handling

- The system shall show clear processing status at the file and batch level.
- The system shall capture transcription, cleanup, summarization, upload, and export errors.
- The system shall keep failed files visible with retry actions and diagnostic messages.
- The system shall prevent export until at least one transcript section is complete.

### 4.15 Security and Data Retention

- The system shall store secrets only in environment variables or a local ignored `.env` file.
- The system shall not log API keys or credentials.
- The system shall store uploaded audio and generated text locally by default.
- The system shall provide a retention policy for uploaded audio, intermediate transcripts, and final outputs.
- The system should provide manual delete controls for source audio and generated runs.

## 5. Non-Functional Requirements

- Accuracy: transcription should prioritize high accuracy over speed for long-form travel book material, especially names of places, landmarks, people, dates, and local terms.
- Reliability: failed processing steps should be recoverable without losing completed sections.
- Performance: the UI should remain responsive during long transcription jobs.
- Usability: upload, ordering, travel metadata review, transcript review, and export should be simple enough for non-technical users.
- Portability: the app should run locally on macOS and be deployable to a cloud host later.
- Observability: the app should write structured processing logs without storing secrets.

## 6. Recommended Speech-to-Text Requirements

- Preferred production options: Azure AI Speech or OpenAI transcription APIs, depending on desired language controls, privacy posture, and cost.
- Preferred local/offline option: Whisper or faster-whisper with a model size selected for the machine's CPU/GPU capacity.
- The transcription layer should be provider-abstracted so the application can switch engines without changing the UI or output workflow.

## 7. Acceptance Criteria

- A user can log in and upload one MP3 file from `SampleVoice/`.
- A user can upload multiple files, reorder them, and process them sequentially.
- Each completed file produces a raw transcript and cleaned transcript.
- A user can add or correct trip, country, city, place, visit date, and route order metadata.
- Combined output follows the selected route order and includes travel section or chapter headings.
- The system can export at least one blog-post draft and one book-chapter draft from the same reviewed transcript section.
- Output files are written under `voiceoutput/` with timestamped names.
- The system can generate a summary and a print/PDF-ready view.
- Errors are visible and do not erase successful transcripts from the same batch.
- No credential values are printed in logs or saved in generated output.

## 8. Current Workspace Findings

- `SampleVoice/` exists.
- `voiceoutput/` exists.
- One sample MP3 file exists under `SampleVoice/`.
- No existing project code or documentation files were present before this SRS was created.
- Local transcription could not be performed yet because `ffmpeg`, `ffprobe`, Whisper CLI, faster-whisper, and speech provider credentials are not configured.