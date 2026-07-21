# Janat — sandbox · Part 2 · TTS

Scratch space for experiments, voice samples, notebooks, notes.

Your production code goes in **`backend/app/tts.py`** — implement:

```python
def synthesize(text: str, *, voice: str | None = None) -> bytes: ...  # returns mp3
```

ElevenLabs / OpenAI TTS / XTTS-v2 / Fish Speech — your choice. Return mp3 bytes
and the pipeline plays it back automatically (no other file to touch).
Bonus: add `synthesize_stream(text)` for streaming playback — see docs/ARCHITECTURE.md.
