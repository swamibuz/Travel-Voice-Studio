from app.cleanup.glossary import apply_travel_glossary
from app.cleanup.service import clean_transcript


def test_apply_travel_glossary_corrects_known_terms() -> None:
    text = "In Sarojiya we heard about Frank Ferdinand and Yogaslava before going to Ergi Govina."
    corrected = apply_travel_glossary(text)
    assert "Sarajevo" in corrected
    assert "Franz Ferdinand" in corrected
    assert "Yugoslavia" in corrected
    assert "Herzegovina" in corrected


def test_clean_transcript_preserves_raw_meaning_with_glossary() -> None:
    cleaned = clean_transcript("Sarojiya was then in Yogaslava.")
    assert cleaned.startswith("Cleaned English Transcript")
    assert "Sarajevo was then in Yugoslavia" in cleaned
