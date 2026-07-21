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

from collections.abc import AsyncIterator


class TTSNotImplemented(RuntimeError):
    pass


def synthesize(text: str, *, voice: str | None = None) -> bytes:
    """Convert the agent's answer to speech. Implement me (Part 2)."""
    raise TTSNotImplemented(
        "TTS is not wired yet. Implement synthesize() in backend/app/tts.py "
        "(Part 2). See the docstring for the expected contract."
    )


async def synthesize_stream(
    text: str, *, voice: str | None = None
) -> AsyncIterator[bytes]:
    """
    Bonus (streaming TTS): yield mp3 chunks as they are generated so the
    frontend can start playing before the whole answer is synthesized.

    Reference wiring for ElevenLabs streaming is below (commented). Janat: swap in
    your provider (ElevenLabs stream / OpenAI TTS / XTTS-v2 / Fish Speech stream)
    and `yield` each audio chunk.

    Default behaviour: if you haven't implemented streaming yet but HAVE implemented
    the batch `synthesize()`, we fall back to synthesizing once and yielding it as a
    single chunk — so the streaming endpoint still works.
    """
    # --- reference: ElevenLabs streaming (uncomment + set keys to use) ---
    # import os
    # from elevenlabs.client import ElevenLabs
    # client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    # stream = client.text_to_speech.stream(
    #     text=text,
    #     voice_id=voice or os.environ["ELEVENLABS_VOICE_ID"],
    #     model_id="eleven_turbo_v2_5",
    #     output_format="mp3_44100_128",
    # )
    # for chunk in stream:
    #     if chunk:
    #         yield chunk
    # return

    # fallback: reuse batch synthesize() if it exists, else signal not-implemented
    audio = synthesize(text, voice=voice)  # raises TTSNotImplemented if neither is wired
    yield audio
