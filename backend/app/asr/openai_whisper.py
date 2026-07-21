"""Облачный ASR через OpenAI Audio API.

По состоянию на июль 2026 рекомендованная модель — gpt-4o-mini-transcribe
(whisper-1 помечен как legacy). Лимит файла — 25 MB.

Примечание: verbose_json (сегменты/word-таймстемпы) поддерживает только
whisper-1, поэтому для gpt-4o-* моделей возвращаем плоский текст.
"""
import logging

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_ASR_MODEL
from .base import ASRProvider, Segment, TranscriptionResult

logger = logging.getLogger(__name__)

# Промпт-подсказка декодеру: доменные термины нашего ассистента,
# чтобы Whisper не коверкал названия мест и площадок
DOMAIN_PROMPT = (
    "Разговор о планировании досуга: концерты, стендап, кино, выставки, "
    "афиша, билеты, Алматы, Астана, sxodim, ticketon."
)


class OpenAIWhisperASR(ASRProvider):
    def __init__(self, model: str = OPENAI_ASR_MODEL):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY не задан (положите его в backend/.env)")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        kwargs: dict = {
            "model": self.model,
            "prompt": DOMAIN_PROMPT,
            "temperature": 0.0,
        }
        if language:
            kwargs["language"] = language

        # verbose_json с сегментами доступен только у whisper-1
        use_verbose = self.model == "whisper-1"
        if use_verbose:
            kwargs["response_format"] = "verbose_json"
            kwargs["timestamp_granularities"] = ["segment"]

        with open(audio_path, "rb") as f:
            result = self.client.audio.transcriptions.create(file=f, **kwargs)

        segments = []
        duration = None
        detected_language = language
        if use_verbose:
            duration = getattr(result, "duration", None)
            detected_language = getattr(result, "language", language)
            for s in getattr(result, "segments", None) or []:
                segments.append(Segment(start=s.start, end=s.end, text=s.text.strip()))

        return TranscriptionResult(
            text=result.text.strip(),
            language=detected_language,
            duration=duration,
            provider="openai",
            model=self.model,
            segments=segments,
        )
