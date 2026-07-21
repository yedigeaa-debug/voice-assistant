"""
Part 2 — TTS (Text-to-Speech), implemented with coqui XTTS-v2. Owner: Janat.

Contract (used by main.py — unchanged):
    synthesize(text: str, *, voice: str | None = None) -> bytes   # mp3
    synthesize_stream(text, *, voice=None) -> AsyncIterator[bytes]  # mp3 chunks

Engine: XTTS-v2 (`tts_models/multilingual/multi-dataset/xtts_v2`), one
consistent voice across languages. Language is auto-detected per answer:

    en, ru  -> native XTTS voices
    kk      -> phonetic bridge: Kazakh numbers -> Kazakh words, Kazakh-only
               letters -> closest Russian graphemes, spoken by the Russian
               voice (XTTS has no native Kazakh). See tts_text.py.

Naturalness: sentence-aware chunking under the model's per-language char
limits, ~220 ms pauses between chunks, enforced terminal punctuation.

Env knobs:
    XTTS_SPEAKER      built-in voice name (default "Claribel Dervla")
    XTTS_SPEAKER_WAV  path to a 6+ s wav -> clones that voice instead
    XTTS_DEVICE       cpu (default) / cuda / mps
    TTS_LANG          force language code, skip auto-detection

First call downloads the model (~1.8 GB) to the standard TTS cache; the
download is skipped if it's already there.
"""

from __future__ import annotations

import asyncio
import io
import os
import threading
from collections.abc import AsyncIterator

import numpy as np

from .tts_text import chunk_text, detect_language, prepare_kazakh

os.environ.setdefault("COQUI_TOS_AGREED", "1")

SAMPLE_RATE = 24_000                      # XTTS-v2 native output rate
_GAP_SEC = 0.22                           # breathing pause between chunks
_CHAR_LIMIT = {"en": 230, "ru": 170}      # model's own limits are 250/182
_DEFAULT_SPEAKER = os.environ.get("XTTS_SPEAKER", "Claribel Dervla")

_model = None
_model_lock = threading.Lock()


class TTSNotImplemented(RuntimeError):
    """Kept for interface compatibility (main.py catches it). Raised only if
    the TTS dependencies are missing."""


def _get_model():
    global _model
    with _model_lock:
        if _model is None:
            try:
                from TTS.api import TTS
            except ImportError as e:  # pragma: no cover
                raise TTSNotImplemented(
                    "TTS deps missing: pip install 'coqui-tts[codec]' torch torchaudio"
                ) from e
            device = os.environ.get("XTTS_DEVICE", "cpu")
            _model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        return _model


# ----------------------------------------------------------------- public --

def synthesize(text: str, *, voice: str | None = None) -> bytes:
    """Convert the agent's answer to speech. Returns mp3 bytes."""
    pieces = list(_synth_pieces(text, voice))
    if not pieces:
        return b""
    gap = np.zeros(int(_GAP_SEC * SAMPLE_RATE), dtype=np.float32)
    joined: list[np.ndarray] = []
    for wav in pieces:
        joined += [wav, gap]
    return _encode_mp3(np.concatenate(joined[:-1]))


async def synthesize_stream(
    text: str, *, voice: str | None = None
) -> AsyncIterator[bytes]:
    """Bonus (streaming): yield an mp3 chunk per synthesized text chunk, so the
    frontend starts playing while the rest is still being generated."""
    lang, chunks = _plan(text)
    for chunk in chunks:
        wav = await asyncio.to_thread(_synth_chunk, chunk, lang, voice)
        yield _encode_mp3(_with_gap(wav))


# --------------------------------------------------------------- internal --

def _plan(text: str) -> tuple[str, list[str]]:
    """Detect language, apply the Kazakh bridge, chunk. -> (xtts_lang, chunks)"""
    lang = os.environ.get("TTS_LANG") or detect_language(text)
    if lang == "kk":
        text, lang = prepare_kazakh(text), "ru"
    return lang, chunk_text(text, _CHAR_LIMIT.get(lang, 170))


def _synth_chunk(chunk: str, lang: str, voice: str | None) -> np.ndarray:
    model = _get_model()
    kwargs = dict(text=chunk, language=lang, split_sentences=False)
    speaker_wav = os.environ.get("XTTS_SPEAKER_WAV")
    if voice and voice.endswith(".wav"):
        kwargs["speaker_wav"] = voice          # clone from a reference sample
    elif speaker_wav:
        kwargs["speaker_wav"] = speaker_wav
    else:
        kwargs["speaker"] = voice or _DEFAULT_SPEAKER
    return np.asarray(model.tts(**kwargs), dtype=np.float32)


def _synth_pieces(text: str, voice: str | None):
    lang, chunks = _plan(text)
    for chunk in chunks:
        yield _synth_chunk(chunk, lang, voice)


def _with_gap(wav: np.ndarray) -> np.ndarray:
    return np.concatenate([wav, np.zeros(int(_GAP_SEC * SAMPLE_RATE), np.float32)])


def _encode_mp3(audio: np.ndarray, rate: int = SAMPLE_RATE) -> bytes:
    """float32 mono [-1, 1] -> mp3 bytes (PyAV, no external ffmpeg binary)."""
    import av

    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)[np.newaxis, :]
    buf = io.BytesIO()
    with av.open(buf, "w", format="mp3") as container:
        stream = container.add_stream("libmp3lame", rate=rate)
        stream.layout = "mono"
        frame = av.AudioFrame.from_ndarray(pcm, format="s16p", layout="mono")
        frame.sample_rate = rate
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode(None):      # flush
            container.mux(packet)
    return buf.getvalue()
