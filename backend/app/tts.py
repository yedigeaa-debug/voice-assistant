"""
Part 2 — TTS (Text-to-Speech) INTERFACE.

Owned by the TTS teammate. Parts 3 & 4 only depend on the `synthesize`
signature below — implement it with ElevenLabs, OpenAI TTS, XTTS-v2,
Fish Speech, etc. Return raw mp3 bytes and the pipeline plays it back.

Contract:
    synthesize(text: str, *, voice: str | None = None) -> bytes
        text   : the agent's answer to speak
        voice  : optional voice id / name (provider-specific)
        returns: mp3 audio bytes

Streaming (bonus): add an async generator variant, e.g.
    async def synthesize_stream(text) -> AsyncIterator[bytes]
and stream chunks back over the /api/chat/stream endpoint. See ARCHITECTURE.md.
"""

from __future__ import annotations


class TTSNotImplemented(RuntimeError):
    pass


def synthesize(text: str, *, voice: str | None = None) -> bytes:
    """Convert the agent's answer to speech. Implement me (Part 2)."""
    raise TTSNotImplemented(
        "TTS is not wired yet. Implement synthesize() in backend/app/tts.py "
        "(Part 2). See the docstring for the expected contract."
    )
