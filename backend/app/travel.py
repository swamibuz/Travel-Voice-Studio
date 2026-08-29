from __future__ import annotations

import re
from pathlib import Path


def title_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = re.sub(r"[_-]+", " ", stem)
    cleaned = re.sub(r"\b(audio|voice|recording)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() or "Travel Voice Note"


def infer_metadata(filename: str, order_index: int) -> dict[str, object]:
    title = title_from_filename(filename)
    date_match = re.search(r"(20\d{2})[-_ ]?(\d{2})[-_ ]?(\d{2})", filename)
    visit_date = ""
    if date_match:
        visit_date = "-".join(date_match.groups())
    return {
        "inferred_title": title,
        "route_order": order_index + 1,
        "visit_date": visit_date,
        "blog_title": f"Travel Notes: {title}",
        "chapter_title": f"Chapter {order_index + 1}: {title}",
    }


def display_location(row: dict[str, object]) -> str:
    parts = [str(row.get(key, "")).strip() for key in ("place_name", "city", "country")]
    return ", ".join(part for part in parts if part) or "Location to be reviewed"
