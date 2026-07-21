"""Фабрика ASR-провайдеров. Провайдеры кэшируются (модель грузится один раз)."""
from functools import lru_cache

from ..config import ASR_PROVIDER
from .base import ASRProvider, TranscriptionResult

__all__ = ["get_asr", "ASRProvider", "TranscriptionResult"]


@lru_cache(maxsize=2)
def get_asr(provider: str | None = None) -> ASRProvider:
    name = (provider or ASR_PROVIDER).lower()
    if name == "openai":
        from .openai_whisper import OpenAIWhisperASR
        return OpenAIWhisperASR()
    if name == "local":
        from .local_whisper import LocalWhisperASR
        return LocalWhisperASR()
    raise ValueError(f"Неизвестный ASR-провайдер: {name!r} (ожидается 'local' или 'openai')")
