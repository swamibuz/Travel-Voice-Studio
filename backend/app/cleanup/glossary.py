from __future__ import annotations

import re


DEFAULT_TRAVEL_GLOSSARY: tuple[tuple[str, str], ...] = (
    ("Sarojiya", "Sarajevo"),
    ("Sarojiyo", "Sarajevo"),
    ("Saroji", "Sarajevo"),
    ("Frank Ferdinand", "Franz Ferdinand"),
    ("Yogaslava", "Yugoslavia"),
    ("Sarbania Army", "Bosnian Army"),
    ("seas by the", "siege by the"),
    ("Memento Sauvagnas", "memento souvenirs"),
    ("Republica Spurska", "Republika Srpska"),
    ("Pardah", "purdah"),
    ("Rijab", "hijab"),
    ("added scars", "headscarves"),
    ("soignias", "souvenirs"),
    ("Ergi Govina", "Herzegovina"),
    ("asking for arms", "asking for alms"),
)


def apply_travel_glossary(text: str) -> str:
    corrected = text
    for source, target in DEFAULT_TRAVEL_GLOSSARY:
        corrected = re.sub(re.escape(source), target, corrected, flags=re.IGNORECASE)
    return corrected
