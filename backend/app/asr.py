"""
Part 1 — ASR (Speech-to-Text) INTERFACE.

This file is owned by the ASR teammate. Parts 3 & 4 only depend on the
`transcribe` function signature below — implement it however you like
(OpenAI Whisper API, faster-whisper, nvidia/parakeet, ...), and the rest of
the pipeline keeps working with no other changes.

Contract:
    transcribe(audio: bytes, *, content_type: str) -> str
        audio        : raw bytes of the uploaded recording (e.g. webm/opus, wav)
        content_type : MIME type the browser sent (e.g. "audio/webm")
        returns      : the recognized text (may be "" if nothing was heard)

Hyperparameter hints from the spec (Whisper-based):
    language="ru" or auto, beam_size=5 (drop to 1 for greedy/faster),
    temperature=0.0, condition_on_previous_text=False for long/looping audio.
"""

from __future__ import annotations


class ASRNotImplemented(RuntimeError):
    pass


def transcribe(audio: bytes, *, content_type: str = "audio/webm") -> str:
    """Convert user audio to text. Implement me (Part 1)."""
    raise ASRNotImplemented(
        "ASR is not wired yet. Implement transcribe() in backend/app/asr.py "
        "(Part 1). See the docstring for the expected contract."
    )
