# Dana — sandbox · Part 1 · ASR / STT

Scratch space for experiments, model downloads, notebooks, notes.

Your production code goes in **`backend/app/asr.py`** — implement:

```python
def transcribe(audio: bytes, *, content_type: str = "audio/webm") -> str: ...
```

Whisper API / faster-whisper / nvidia-parakeet — your choice. Once it returns
text, the whole pipeline uses it automatically (no other file to touch).
Bonus: streaming ASR over the `/ws/asr` WebSocket in `main.py`.
