"""Formats Whisper segments into the display format the app shows to users:

    # <title>
    <recorded date and time>

    (0:00) First sentence... (0:14) Next sentence...

    (0:32) New paragraph starts after a longer pause...
"""
from __future__ import annotations

from datetime import datetime

# A pause at least this long between two segments starts a new paragraph.
PARAGRAPH_PAUSE_SECONDS = 3.5
# Safety cap so a paragraph doesn't grow unbounded during long uninterrupted speech.
MAX_SENTENCES_PER_PARAGRAPH = 8


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes}:{secs:02d}"


def format_recorded_at(recorded_at: str | None) -> str:
    if not recorded_at:
        return ""
    try:
        value = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
    except ValueError:
        return recorded_at
    # Manual formatting (not %-d/%-I) so this works the same on Windows and Linux.
    hour_12 = value.hour % 12 or 12
    am_pm = "AM" if value.hour < 12 else "PM"
    return f"{value.strftime('%b')} {value.day}, {value.year}, {hour_12}:{value.minute:02d} {am_pm}"


def build_paragraphs(segments: list[dict[str, object]]) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    previous_end: float | None = None

    for segment in segments:
        start = float(segment["start"])
        text = str(segment["text"]).strip()
        if not text:
            continue
        gap = start - previous_end if previous_end is not None else 0
        if current and (gap >= PARAGRAPH_PAUSE_SECONDS or len(current) >= MAX_SENTENCES_PER_PARAGRAPH):
            paragraphs.append(" ".join(current))
            current = []
        current.append(f"({format_timestamp(start)}) {text}")
        previous_end = float(segment["end"])

    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def format_transcript(title: str, recorded_at: str | None, segments: list[dict[str, object]]) -> str:
    header = [f"# {title}"]
    date_line = format_recorded_at(recorded_at)
    if date_line:
        header.append(date_line)

    paragraphs = build_paragraphs(segments)
    body = "\n\n".join(paragraphs) if paragraphs else "(No speech detected in this recording.)"
    return "\n".join(header) + "\n\n" + body
