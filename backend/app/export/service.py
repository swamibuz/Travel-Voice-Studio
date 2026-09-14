from __future__ import annotations

import html
import json


def build_markdown(title: str, sections: list[dict[str, object]], field: str) -> str:
    chunks = [f"# {title}\n"]
    for section in sections:
        heading = section.get("chapter_title") or section.get("blog_title") or section.get("inferred_title") or section.get("original_name")
        location = section.get("location") or "Location to be reviewed"
        chunks.append(f"\n## {heading}\n\n")
        chunks.append(f"**Location:** {location}\n\n")
        chunks.append(str(section.get(field, "")).strip())
        chunks.append("\n")
    return "".join(chunks)


def build_printable_html(title: str, sections: list[dict[str, object]], include_raw: bool) -> str:
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
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        "<style>body{font-family:Georgia,serif;max-width:820px;margin:40px auto;line-height:1.6;color:#222}"
        "section{break-inside:avoid;margin-bottom:32px}h1,h2{line-height:1.2}@media print{body{margin:0}}</style>"
        f"</head><body><h1>{html.escape(title)}</h1>{''.join(body)}</body></html>"
    )


def build_metadata_json(sections: list[dict[str, object]]) -> str:
    return json.dumps({"sections": sections}, indent=2)

