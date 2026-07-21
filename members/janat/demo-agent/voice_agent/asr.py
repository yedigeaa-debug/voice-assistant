"""Speech recognition via faster-whisper (en / ru / kk auto-detected)."""

from __future__ import annotations

import os

from .lang import detect_language


class Listener:
    """Lazy-loading Whisper transcriber."""

    def __init__(self, model_size: str | None = None):
        # `small` is a good CPU speed/quality balance; override for Kazakh-heavy
        # use with WHISPER_MODEL=medium (kk accuracy improves a lot).
        self.model_size = model_size or os.environ.get("WHISPER_MODEL", "small")
        self._model = None

    def _whisper(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device="cpu",
                                       compute_type="int8")
        return self._model

    def transcribe(self, wav_path: str) -> tuple[str, str]:
        """Return (text, language) where language is 'en' / 'ru' / 'kk'."""
        segments, info = self._whisper().transcribe(wav_path, beam_size=5,
                                                    vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments).strip()

        lang = info.language if info.language in ("en", "ru", "kk") else None
        # Whisper often mislabels Kazakh as Russian; the transcript itself is
        # a stronger signal (Kazakh-specific letters / stopwords).
        text_lang = detect_language(text) if text else "en"
        if lang == "ru" and text_lang == "kk":
            lang = "kk"
        return text, lang or text_lang


def record(wav_path: str, seconds: float = 5.0, samplerate: int = 16_000) -> str:
    """Record `seconds` of microphone audio into a wav file."""
    import sounddevice as sd
    import soundfile as sf

    print(f"🎙  Listening for {seconds:.0f}s ... speak now")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate,
                   channels=1, dtype="float32")
    sd.wait()
    sf.write(wav_path, audio, samplerate)
    return wav_path
