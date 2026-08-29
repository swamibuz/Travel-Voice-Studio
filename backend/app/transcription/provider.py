from __future__ import annotations

from pathlib import Path

from ..config import TRANSCRIPTION_LANGUAGE_HINT, TRANSCRIPTION_PROMPT_HINT, TRANSCRIPTION_PROVIDER, WHISPER_MODEL


def transcribe_audio(audio_path: str, original_name: str, metadata: dict[str, object]) -> str:
    provider = TRANSCRIPTION_PROVIDER.lower().strip()
    if provider in {"faster-whisper", "whisper-local", "local"}:
        return faster_whisper_transcript(audio_path)
    return demo_transcript(audio_path, original_name, metadata, provider)


def faster_whisper_transcript(audio_path: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Install faster-whisper or set TRANSCRIPTION_PROVIDER=demo") from exc

    language = "en" if TRANSCRIPTION_LANGUAGE_HINT.lower().startswith("en") else None
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
        initial_prompt=TRANSCRIPTION_PROMPT_HINT,
    )
    lines = [
        f"[Transcribed with faster-whisper model '{WHISPER_MODEL}'. Detected language: {info.language}.]",
        "",
    ]
    for segment in segments:
        text = segment.text.strip()
        if text:
            lines.append(text)
    return "\n".join(lines).strip()


def demo_transcript(audio_path: str, original_name: str, metadata: dict[str, object], provider: str) -> str:
    size = Path(audio_path).stat().st_size if Path(audio_path).exists() else 0
    title = metadata.get("inferred_title") or original_name
    location = ", ".join(
        str(metadata.get(key, "")).strip()
        for key in ("place_name", "city", "country")
        if str(metadata.get(key, "")).strip()
    ) or "a place from the trip"
    return (
        f"[Demo transcript generated because provider '{provider}' is not configured for live speech-to-text.]\n\n"
        f"Source file: {original_name}\n"
        f"Detected title: {title}\n"
        f"Language hint: {TRANSCRIPTION_LANGUAGE_HINT}\n"
        f"Prompt hint: {TRANSCRIPTION_PROMPT_HINT}\n"
        f"Audio bytes stored: {size}\n\n"
        f"Today I am documenting my visit to {location}. I want to capture what I saw, "
        "how the place felt, the people I met, the food and culture I noticed, and the "
        "small practical details that will help me later turn this travel memory into a blog "
        "post and a chapter in my book."
    )
