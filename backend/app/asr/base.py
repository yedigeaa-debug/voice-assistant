"""Общий интерфейс ASR-провайдеров."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str
    language: str | None = None
    duration: float | None = None
    provider: str = ""
    model: str = ""
    segments: list[Segment] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "duration": self.duration,
            "provider": self.provider,
            "model": self.model,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text} for s in self.segments
            ],
        }


class ASRProvider(ABC):
    """Переводит аудиофайл в текст."""

    @abstractmethod
    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        ...
