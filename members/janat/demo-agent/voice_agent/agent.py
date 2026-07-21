"""End-to-end voice agent: microphone -> Whisper -> brain -> XTTS-v2 -> speaker."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from . import asr, brain
from .lang import detect_language
from .tts import Speaker


class VoiceAgent:
    def __init__(self, speaker_wav: str | None = None, city: str = "almaty"):
        self.listener = asr.Listener()
        self.speaker = Speaker(speaker_wav=speaker_wav)
        self.city = city

    # ------------------------------------------------------------ pieces --

    def hear(self, wav_path: str) -> tuple[str, str]:
        """Transcribe user speech -> (text, language)."""
        return self.listener.transcribe(wav_path)

    def think(self, question: str, language: str | None = None) -> tuple[str, str]:
        """Question text -> (answer text, language)."""
        language = language or detect_language(question)
        return brain.answer(question, language, self.city), language

    def say(self, text: str, language: str | None = None,
            out_path: str | None = None) -> str:
        """Answer text -> wav file path."""
        language = language or detect_language(text)
        out_path = out_path or tempfile.mktemp(suffix=".wav", prefix="agent_")
        return self.speaker.synthesize(text, language, out_path)

    # ------------------------------------------------------------- flows --

    def ask(self, question: str, out_path: str | None = None,
            play: bool = True, language: str | None = None) -> tuple[str, str]:
        """Text question -> spoken answer. Returns (answer_text, wav_path)."""
        answer, language = self.think(question, language)
        print(f"[{language}] {answer}")
        wav = self.say(answer, language, out_path)
        if play:
            play_wav(wav)
        return answer, wav

    def voice_turn(self, seconds: float = 5.0, out_path: str | None = None,
                   play: bool = True) -> tuple[str, str, str]:
        """One full voice interaction. Returns (question, answer, wav_path)."""
        mic = tempfile.mktemp(suffix=".wav", prefix="mic_")
        asr.record(mic, seconds=seconds)
        question, language = self.hear(mic)
        Path(mic).unlink(missing_ok=True)
        if not question:
            question, language = "", "en"
            print("…didn't catch that.")
        else:
            print(f"🗣  [{language}] {question}")
        answer, language = self.think(question, language)
        print(f"🤖 [{language}] {answer}")
        wav = self.say(answer, language, out_path)
        if play:
            play_wav(wav)
        return question, answer, wav


def play_wav(path: str) -> None:
    """Play audio: afplay on macOS, else best-effort via sounddevice."""
    if sys.platform == "darwin":
        subprocess.run(["afplay", path], check=False)
        return
    try:
        import sounddevice as sd
        import soundfile as sf
        data, rate = sf.read(path, dtype="float32")
        sd.play(data, rate)
        sd.wait()
    except Exception:
        print(f"(saved to {path})")
