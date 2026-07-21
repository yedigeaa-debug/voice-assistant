"""Локальный ASR на faster-whisper (CTranslate2-имплементация Whisper).

Гиперпараметры выставлены по рекомендациям семинара:
- beam_size=5 — стандарт; уменьшите до 1 (greedy) ради скорости;
- temperature=[0.0, 0.2, 0.4] — fallback-массив против галлюцинаций/зацикливания;
- condition_on_previous_text=False — защита от "залипания" на длинных аудио.
"""
import logging

from faster_whisper import WhisperModel

from ..config import LOCAL_ASR_COMPUTE, LOCAL_ASR_DEVICE, LOCAL_ASR_MODEL
from .base import ASRProvider, Segment, TranscriptionResult

logger = logging.getLogger(__name__)


class LocalWhisperASR(ASRProvider):
    def __init__(
        self,
        model_size: str = LOCAL_ASR_MODEL,
        device: str = LOCAL_ASR_DEVICE,
        compute_type: str = LOCAL_ASR_COMPUTE,
        beam_size: int = 5,
        condition_on_previous_text: bool = False,
    ):
        logger.info("Loading faster-whisper '%s' (device=%s, compute=%s)…",
                    model_size, device, compute_type)
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.model_size = model_size
        self.beam_size = beam_size
        self.condition_on_previous_text = condition_on_previous_text
        logger.info("faster-whisper loaded")

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        segments_iter, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=self.beam_size,
            temperature=[0.0, 0.2, 0.4],
            condition_on_previous_text=self.condition_on_previous_text,
            vad_filter=True,  # отсекаем тишину — быстрее и чище для голосовых команд
        )
        segments = [Segment(start=s.start, end=s.end, text=s.text.strip()) for s in segments_iter]
        text = " ".join(s.text for s in segments).strip()
        return TranscriptionResult(
            text=text,
            language=info.language,
            duration=info.duration,
            provider="local",
            model=f"faster-whisper-{self.model_size}",
            segments=segments,
        )
