from __future__ import annotations

import re


DEFAULT_TRAVEL_GLOSSARY: tuple[tuple[str, str], ...] = (
    ("Sarojia", "Sarajevo"),
    ("Sarojiava", "Sarajevo"),
    ("Sarojiya", "Sarajevo"),
    ("Sarojiyo", "Sarajevo"),
    ("Saroji", "Sarajevo"),
    ("Frank Ferdinand", "Franz Ferdinand"),
    ("Yogaslava", "Yugoslavia"),
    ("Sarbania Army", "Bosnian Army"),
    ("seas by the", "siege by the"),
    ("Memento Sauvagnas", "memento souvenirs"),
    ("Republica Spurska", "Republika Srpska"),
    ("Republika Sperska", "Republika Srpska"),
    ("Pardah", "purdah"),
    ("parda", "purdah"),
    ("Rijab", "hijab"),
    ("added scars", "headscarves"),
    ("head scars", "headscarves"),
    ("soignias", "souvenirs"),
    ("Ergi Govina", "Herzegovina"),
    ("Argygovina", "Herzegovina"),
    ("asking for arms", "asking for alms"),
    ("autotourism dictators", "authoritarian dictators"),
    ("communist obroes", "communist top brass"),
)


def apply_travel_glossary(text: str) -> str:
    corrected = text
    for source, target in DEFAULT_TRAVEL_GLOSSARY:
        corrected = re.sub(re.escape(source), lambda match, replacement=target: replacement, corrected, flags=re.IGNORECASE)
    return corrected
