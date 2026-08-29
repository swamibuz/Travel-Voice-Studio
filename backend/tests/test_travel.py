from app.travel import infer_metadata, title_from_filename


def test_title_from_filename_removes_audio_noise() -> None:
    assert title_from_filename("AUDIO-2026-08-29-18-28-45_0506.mp3") == "2026 08 29 18 28 45 0506"


def test_infer_metadata_extracts_date_and_titles() -> None:
    metadata = infer_metadata("paris-2026-08-29.mp3", 2)
    assert metadata["visit_date"] == "2026-08-29"
    assert metadata["route_order"] == 3
    assert str(metadata["blog_title"]).startswith("Travel Notes:")
