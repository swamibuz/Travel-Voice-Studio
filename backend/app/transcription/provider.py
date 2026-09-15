from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from ..config import TRANSCRIPTION_LANGUAGE_HINT, TRANSCRIPTION_PROMPT_HINT, TRANSCRIPTION_PROVIDER, WHISPER_MODEL

logger = logging.getLogger(__name__)
_model_cache: dict[str, object] = {}


def transcribe_audio(audio_path: str, original_name: str, metadata: dict[str, object]) -> str:
    """Backward-compatible plain-text transcript (used by tests/older callers)."""
    provider = TRANSCRIPTION_PROVIDER.lower().strip()
    if provider in {"faster-whisper", "whisper-local", "local"}:
        segments = transcribe_audio_segments(audio_path)
        return "\n".join(segment["text"] for segment in segments if segment["text"])
    return demo_transcript(audio_path, original_name, metadata, provider)


def _to_wav(audio_path: str) -> str:
    """Re-encodes the upload to mono 16kHz WAV via ffmpeg before handing it to
    Whisper. Voice-recorder apps often produce MP3/M4A files with variable
    bitrate or non-standard headers; PyAV/ctranslate2 can misjudge the total
    duration for those and stop transcribing partway through. Ffmpeg's decoder
    reads the full stream correctly, so pre-converting avoids the truncation.
    """
    wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(wav_fd)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ar", "16000", "-vn", wav_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        return wav_path
    except FileNotFoundError:
        logger.warning("ffmpeg not found on PATH — transcribing the original file directly, "
                        "which can truncate recordings with non-standard MP3/M4A headers.")
        Path(wav_path).unlink(missing_ok=True)
        return audio_path
    except subprocess.CalledProcessError as exc:
        logger.warning("ffmpeg failed (%s) — transcribing the original file directly.", exc.stderr)
        Path(wav_path).unlink(missing_ok=True)
        return audio_path



def _load_model():
    from faster_whisper import WhisperModel

    if WHISPER_MODEL not in _model_cache:
        _model_cache[WHISPER_MODEL] = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model_cache[WHISPER_MODEL]


def transcribe_audio_segments(audio_path: str) -> list[dict[str, object]]:
    """Returns [{start, end, text}, ...] covering the entire recording."""
    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Install faster-whisper or set TRANSCRIPTION_PROVIDER=demo") from exc

    language = "en" if TRANSCRIPTION_LANGUAGE_HINT.lower().startswith("en") else None
    model = _load_model()
    wav_path = _to_wav(audio_path)
    try:
        segments, _info = model.transcribe(
            wav_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            # Prevents the decoder from anchoring on earlier (possibly low-quality) text
            # and prematurely giving up partway through longer recordings.
            condition_on_previous_text=False,
            initial_prompt=TRANSCRIPTION_PROMPT_HINT,
        )
        results: list[dict[str, object]] = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                results.append({"start": segment.start, "end": segment.end, "text": text})
        return results
    finally:
        if wav_path != audio_path:
            Path(wav_path).unlink(missing_ok=True)


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
