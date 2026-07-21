"""
Adapter that bridges Dana's provider-based ASR (get_asr().transcribe(path)) to the
simple bytes->str contract the pipeline (main.py, realtime_asr fallback) expects.

    transcribe(audio: bytes, *, content_type=...) -> str

Keeps `ASRNotImplemented` as the sentinel the orchestrator catches, so if a provider
can't start (e.g. OpenAI key missing and no local model), the pipeline degrades
gracefully instead of 500-ing.
"""

from __future__ import annotations

import tempfile

from ..config import ASR_LANGUAGE
from . import get_asr


class ASRNotImplemented(RuntimeError):
    pass


# map the browser MIME type to a file suffix Whisper/ffmpeg can sniff
_SUFFIX = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
}


def transcribe(audio: bytes, *, content_type: str = "audio/webm") -> str:
    if not audio:
        return ""
    suffix = _SUFFIX.get(content_type.split(";")[0].strip(), ".webm")
    try:
        provider = get_asr()
    except (ValueError, RuntimeError) as e:
        raise ASRNotImplemented(str(e)) from e

    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(audio)
        tmp.flush()
        result = provider.transcribe(tmp.name, language=ASR_LANGUAGE)
    return result.text
