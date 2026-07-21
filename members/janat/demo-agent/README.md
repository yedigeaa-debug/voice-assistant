# Almaty Voice Agent 🎙 (en / ru / kk)

A voice assistant you can *talk to* in **English, Russian or Kazakh**.
Ask it things like *"What interesting events are there in Almaty?"* — it
transcribes your speech with Whisper, pulls the live afisha from
[sxodim.com](https://sxodim.com/almaty), and answers **aloud** with a natural,
high-quality voice synthesized by **coqui XTTS-v2**.

```
🎤 mic ──▶ faster-whisper (ASR, auto en/ru/kk) ──▶ brain
                                                   │  intent → scrape sxodim.com
                                                   │  answer in the user's language
                                                   ▼
🔊 speaker ◀── XTTS-v2 (one consistent voice, all languages) ◀── text
```

## Setup

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

First run downloads XTTS-v2 (~1.8 GB) and Whisper `small` automatically.

## Usage

```bash
# 1) Just make text sound natural (language auto-detected):
python -m voice_agent --say "Сәлем! Алматыға қош келдіңіз!" --out hello.wav

# 2) Text question -> spoken answer about Almaty events:
python -m voice_agent --ask "What interesting events are there in Almaty?"
python -m voice_agent --ask "Алматыда қандай қызықты концерттер бар?"

# 3) Full voice conversation (records mic, answers aloud, loops):
python -m voice_agent --voice --seconds 6
```

Useful flags: `--lang en|ru|kk` (force language), `--no-play`, `--out file.wav`,
`--speaker-wav your_voice.wav` (clone any voice from a 6+ second sample),
`--city astana` (any sxodim city slug).

Optional env vars:

| var | effect |
|---|---|
| `ANTHROPIC_API_KEY` | answers get written by Claude (conversational, grounded in scraped events) instead of templates; `pip install anthropic` |
| `WHISPER_MODEL=medium` | much better Kazakh ASR (default `small`) |

## How Kazakh works (XTTS-v2 has no `kk`!)

XTTS-v2 officially supports 17 languages — Kazakh isn't one of them. The agent
makes it work through a **phonetic bridge** ([voice_agent/kk_text.py](voice_agent/kk_text.py)):

1. numbers are expanded to Kazakh words first (`7000 → жеті мың`) with a tiny
   built-in num2words, so they aren't read in Russian;
2. Kazakh-only letters are mapped to their closest Russian graphemes:
   `і→и, ұ→у, қ→к, ғ→г, ң→н, һ→х`, and the front vowels `ә/ө/ү` become the
   *iotated* `я/ё/ю` after consonants — Russian palatalization fronts the
   vowel, which is acoustically much closer to `[æ ø y]` than plain `а/о/у`;
3. the result is spoken by the model's **Russian** branch.

Since Kazakh phonology is close to Russian and both share the Cyrillic script,
this sounds surprisingly natural — a light "Russian accent" at worst.

Other naturalness engineering ([voice_agent/tts.py](voice_agent/tts.py)):
sentence-aware chunking under XTTS's per-language character limits (long
inputs otherwise rush and glitch), ~220 ms breathing pauses re-inserted
between chunks, enforced terminal punctuation (XTTS trails off without it),
and one consistent voice persona across all three languages. For English
answers, Cyrillic event titles are romanized so the English voice reads them
cleanly.

ASR robustness: Whisper's language ID often confuses Kazakh with Russian, so
the agent re-checks the *transcript* for Kazakh-specific letters/stopwords and
overrides the label ([voice_agent/asr.py](voice_agent/asr.py)).

## Project layout

```
voice_agent/
  lang.py      language ID (kk letters are a fingerprint vs ru)
  kk_text.py   Kazakh num2words + kk→ru phonetic mapping + Cyrillic→Latin
  tts.py       XTTS-v2 wrapper: chunking, pacing, voice cloning
  asr.py       faster-whisper transcription + mic recording
  events.py    sxodim.com scraper (server-rendered .impression-card parsing)
  brain.py     intent detection → events → answer (Claude optional, templates offline)
  agent.py     hear → think → say orchestration
  __main__.py  CLI
```

> **Note**: XTTS-v2 weights are under the Coqui Public Model License
> (non-commercial). Fine for study/research use like this seminar project.
