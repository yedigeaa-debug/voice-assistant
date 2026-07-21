# Dana — sandbox · Part 1 · ASR / STT

Scratch space for experiments, model downloads, notebooks, notes.

✅ **Done & merged.** Your code lives in **`backend/app/asr/`** (provider
abstraction: `base.py`, `openai_whisper.py`, `local_whisper.py`, factory in
`__init__.py`) plus `backend/app/config.py`.

Integration: `asr/adapter.py` exposes `transcribe(bytes) -> str` so the agent
pipeline (parts 3/4) and the real-time bonus call your providers automatically.
Standalone endpoint `POST /api/transcribe` returns the full `TranscriptionResult`.
