# Janat — sandbox · Part 2 · TTS ✅ implemented

**Status: done.** Production code is in **`backend/app/tts.py`** (+ text
helpers in `backend/app/tts_text.py`), engine = **coqui XTTS-v2**, fully
local, no API keys.

```python
synthesize(text, *, voice=None) -> bytes          # mp3  ✅
synthesize_stream(text, *, voice=None) -> chunks  # mp3  ✅ (bonus, streaming)
```

## What's implemented

- **XTTS-v2** (`tts_models/multilingual/multi-dataset/xtts_v2`), one
  consistent voice across languages; `voice` accepts a built-in speaker name
  or a path to a 6+ s wav to **clone any voice**.
- **Language auto-detection** per answer: en / ru native, and **Kazakh via a
  phonetic bridge** (XTTS has no `kk`): Kazakh numbers → Kazakh words
  (`7000 → жеті мың`), Kazakh-only letters → closest Russian graphemes
  (`і→и, қ→к, ғ→г, ң→н, ұ→у, һ→х`, front vowels `ә/ө/ү` → iotated `я/ё/ю`
  after consonants), spoken by the Russian voice.
- **Naturalness**: sentence-aware chunking under XTTS char limits, ~220 ms
  pauses between chunks, enforced terminal punctuation.
- mp3 encoding via PyAV (no external ffmpeg binary needed).
- First call downloads the model (~1.8 GB); empty text returns instantly so
  `/api/health` stays fast.

## In this sandbox

- [`samples/`](samples/) — demo wavs: same voice speaking **en / ru / kk**
  (kk through the bridge).
- [`demo-agent/`](demo-agent/) — standalone experiment that grew into the
  implementation: a full mic → Whisper ASR → sxodim.com events → XTTS voice
  agent, runnable without the backend (`python -m voice_agent --ask "Какие
  интересные события в Алматы?"`). See its README for the write-up.
