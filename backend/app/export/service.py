from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from ..config import OUTPUT_DIR


def create_run_folder(batch_id: int) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = OUTPUT_DIR / f"batch-{batch_id}_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_markdown(path: Path, title: str, sections: list[dict[str, object]], field: str) -> None:
    chunks = [f"# {title}\n"]
    for section in sections:
        heading = section.get("chapter_title") or section.get("blog_title") or section.get("inferred_title")
        location = section.get("location") or "Location to be reviewed"
        chunks.append(f"\n## {heading}\n\n")
        chunks.append(f"**Location:** {location}\n\n")
        chunks.append(str(section.get(field, "")).strip())
        chunks.append("\n")
    path.write_text("".join(chunks), encoding="utf-8")


def write_printable_html(path: Path, title: str, sections: list[dict[str, object]], include_raw: bool) -> None:
    body = []
    for section in sections:
        heading = html.escape(str(section.get("chapter_title") or section.get("inferred_title") or "Travel Section"))
        location = html.escape(str(section.get("location") or "Location to be reviewed"))
        cleaned = html.escape(str(section.get("cleaned_text") or "")).replace("\n", "<br>")
        body.append(f"<section><h2>{heading}</h2><p><strong>Location:</strong> {location}</p><p>{cleaned}</p>")
        if include_raw:
            raw = html.escape(str(section.get("raw_text") or "")).replace("\n", "<br>")
            body.append(f"<details><summary>Raw transcript</summary><p>{raw}</p></details>")
        body.append("</section>")
    path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        "<style>body{font-family:Georgia,serif;max-width:820px;margin:40px auto;line-height:1.6;color:#222}"
        "section{break-inside:avoid;margin-bottom:32px}h1,h2{line-height:1.2}@media print{body{margin:0}}</style>"
        f"</head><body><h1>{html.escape(title)}</h1>{''.join(body)}</body></html>",
        encoding="utf-8",
    )


def write_metadata(path: Path, batch_id: int, sections: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"batch_id": batch_id, "sections": sections}, indent=2), encoding="utf-8")
