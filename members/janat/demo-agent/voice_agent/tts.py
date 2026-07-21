"""XTTS-v2 speech synthesis with natural-sounding output for en / ru / kk.

Naturalness tricks used here:
  * one cloned/built-in voice across all languages (consistent persona);
  * sentence-aware chunking below the model's per-language character limits
    (long inputs otherwise get rushed and glitchy);
  * short silences re-inserted between chunks so pacing sounds human;
  * terminal punctuation enforced (XTTS trails off without it);
  * Kazakh routed through the Russian voice via a phonetic grapheme mapping
    (see kk_text.py) -- XTTS has no native 'kk'.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import soundfile as sf

from .kk_text import prepare_kazakh

os.environ.setdefault("COQUI_TOS_AGREED", "1")  # auto-accept model download ToS

SAMPLE_RATE = 24_000  # XTTS-v2 output rate
_GAP_SEC = 0.22       # inter-chunk pause

# conservative per-language character limits (model's own are 250/182)
_CHAR_LIMIT = {"en": 230, "ru": 170}

_DEFAULT_SPEAKER = "Claribel Dervla"  # pleasant, neutral built-in voice


class Speaker:
    """Lazy-loading wrapper around the XTTS-v2 model."""

    def __init__(self, speaker_wav: str | None = None,
                 speaker: str = _DEFAULT_SPEAKER, device: str | None = None):
        self.speaker_wav = speaker_wav
        self.speaker = speaker
        self.device = device or "cpu"
        self._tts = None

    def _model(self):
        if self._tts is None:
            from TTS.api import TTS  # heavy import -- deferred
            self._tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        return self._tts

    # ------------------------------------------------------------- public --

    def synthesize(self, text: str, language: str, out_path: str) -> str:
        """Synthesize `text` in 'en' / 'ru' / 'kk' into a wav at `out_path`."""
        if language == "kk":
            text, language = prepare_kazakh(text), "ru"

        chunks = _chunk(text, _CHAR_LIMIT.get(language, 170))
        model = self._model()
        gap = np.zeros(int(_GAP_SEC * SAMPLE_RATE), dtype=np.float32)

        pieces: list[np.ndarray] = []
        for chunk in chunks:
            kwargs = dict(text=chunk, language=language, split_sentences=False)
            if self.speaker_wav:
                kwargs["speaker_wav"] = self.speaker_wav
            else:
                kwargs["speaker"] = self.speaker
            wav = np.asarray(model.tts(**kwargs), dtype=np.float32)
            pieces += [wav, gap]

        audio = np.concatenate(pieces[:-1]) if pieces else np.zeros(1, np.float32)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_path, audio, SAMPLE_RATE)
        return out_path


# ------------------------------------------------------------- chunking ----

_SENT_RE = re.compile(r"(?<=[.!?…])\s+")


def _chunk(text: str, limit: int) -> list[str]:
    """Split text into <=limit chunks at sentence, then comma, boundaries."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if text[-1] not in ".!?…":
        text += "."

    chunks: list[str] = []
    buf = ""
    for sent in _SENT_RE.split(text):
        for piece in _split_long(sent, limit):
            if buf and len(buf) + len(piece) + 1 <= limit:
                buf += " " + piece
            else:
                if buf:
                    chunks.append(buf)
                buf = piece
    if buf:
        chunks.append(buf)
    return chunks


def _split_long(sent: str, limit: int) -> list[str]:
    if len(sent) <= limit:
        return [sent]
    # fall back to comma boundaries, then hard cuts
    parts, buf = [], ""
    for frag in re.split(r"(?<=,)\s+", sent):
        while len(frag) > limit:  # pathological fragment -- hard cut on a space
            cut = frag.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            parts.append(frag[:cut])
            frag = frag[cut:].strip()
        if buf and len(buf) + len(frag) + 1 <= limit:
            buf += " " + frag
        else:
            if buf:
                parts.append(buf)
            buf = frag
    if buf:
        parts.append(buf)
    return parts
