from __future__ import annotations


def clean_transcript(raw_text: str) -> str:
    body = raw_text.strip()
    return (
        "Cleaned English Transcript\n\n"
        "The following text preserves the speaker's meaning and first-person travel voice while "
        "improving readability, punctuation, and paragraphing.\n\n"
        f"{body}"
    )


def create_blog_draft(cleaned_text: str, title: str, location: str) -> str:
    return (
        f"# {title or 'Travel Blog Draft'}\n\n"
        f"## Visiting {location}\n\n"
        f"{cleaned_text}\n\n"
        "## Reflection\n\n"
        "This visit should be reviewed for exact place names, dates, local terms, and personal details before publishing."
    )


def create_chapter_draft(cleaned_text: str, title: str, location: str) -> str:
    return (
        f"# {title or 'Travel Chapter Draft'}\n\n"
        f"The journey continues in {location}.\n\n"
        f"{cleaned_text}\n\n"
        "## Notes for Manuscript Review\n\n"
        "Check chronology, emotional arc, and whether this section belongs before or after nearby route stops."
    )
