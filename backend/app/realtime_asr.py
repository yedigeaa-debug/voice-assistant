"""
Bonus — Real-time ASR (streaming) with a lightweight local model.

Drives the /ws/asr WebSocket: the frontend streams raw PCM audio chunks while the
user is still talking; we keep a rolling buffer, re-transcribe it every ~700 ms and
push partial text back so the screen updates live.

Reference model: faster-whisper "small" (CTranslate2 — fast, low memory). If the
package/model isn't available, StreamingTranscriber raises RealtimeASRUnavailable
and the WebSocket falls back to a clear message instead of crashing.

Audio format contract (frontend -> backend): 16-bit little-endian mono PCM at
16 kHz. See frontend/index.html (AudioWorklet downsamples the mic to this).
"""

from __future__ import annotations

import numpy as np

SAMPLE_RATE = 16_000
# Re-run transcription once we've buffered at least this much new audio.
PARTIAL_EVERY_SEC = 0.7
# Keep at most this many seconds of context (rolling window).
MAX_BUFFER_SEC = 30.0


class RealtimeASRUnavailable(RuntimeError):
    pass


def _load_model():
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:  # package not installed
        raise RealtimeASRUnavailable(
            "faster-whisper is not installed. `pip install faster-whisper` to enable "
            "real-time ASR (bonus)."
        ) from e
    # int8 keeps it light on CPU; device="cuda" + compute_type="float16" if a GPU is present.
    return WhisperModel("small", device="cpu", compute_type="int8")


class StreamingTranscriber:
    """
    One instance per WebSocket connection.

        st = StreamingTranscriber(language="ru")
        partial = st.feed(pcm_bytes)   # -> str | None (None if not enough new audio yet)
        text    = st.final()           # -> str (transcribe whatever is buffered, once)
    """

    def __init__(self, language: str | None = "ru") -> None:
        self._model = _load_model()
        self._language = language
        self._buf = np.zeros(0, dtype=np.float32)
        self._since_partial = 0  # samples accumulated since last partial

    def feed(self, pcm_bytes: bytes) -> str | None:
        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        self._buf = np.concatenate([self._buf, samples])
        self._since_partial += len(samples)

        max_samples = int(MAX_BUFFER_SEC * SAMPLE_RATE)
        if len(self._buf) > max_samples:
            self._buf = self._buf[-max_samples:]

        if self._since_partial < PARTIAL_EVERY_SEC * SAMPLE_RATE:
            return None
        self._since_partial = 0
        return self._transcribe()

    def final(self) -> str:
        return self._transcribe()

    def _transcribe(self) -> str:
        if len(self._buf) == 0:
            return ""
        segments, _ = self._model.transcribe(
            self._buf,
            language=self._language,
            beam_size=1,                 # greedy — fastest, good enough for partials
            condition_on_previous_text=False,
            vad_filter=True,             # skip silence, steadier partials
        )
        return "".join(seg.text for seg in segments).strip()
