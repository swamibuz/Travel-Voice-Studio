from __future__ import annotations


def summarize_sections(sections: list[dict[str, object]], summary_type: str) -> str:
    count = len(sections)
    locations = [str(section.get("location", "")).strip() for section in sections]
    locations = [location for location in locations if location]
    location_text = "; ".join(locations) or "locations pending review"
    return (
        f"# {summary_type.title()} Travel Summary\n\n"
        f"This batch contains {count} travel section(s). Places covered: {location_text}.\n\n"
        "## Key Experiences\n\n"
        "Review the cleaned transcripts and chapter drafts to extract memorable moments, people met, food, culture, practical tips, and lessons learned.\n\n"
        "## Next Editorial Step\n\n"
        "Confirm route order, correct place names, and enrich the manuscript with photos or additional notes where available."
    )
