# Contributing — team workflow

This is a group project. The grade includes **teamwork via Git** (branches, PRs,
regular commits from *everyone*). Please follow this so we all get those points.

## 1. One-time setup

```bash
git clone https://github.com/yedigeaa-debug/voice-assistant.git
cd voice-assistant
```

## 2. Branch per task — never commit to `main` directly

Use a short prefix + your name/topic:

```bash
git checkout main
git pull
git checkout -b feat/asr-whisper        # ASR teammate
# or: feat/tts-elevenlabs, fix/agent-timeout, docs/readme ...
```

Branch naming: `feat/…`, `fix/…`, `docs/…`, `chore/…`.

## 3. Commit style (Conventional Commits)

```
feat: add faster-whisper streaming transcription
fix: handle empty audio upload in /api/chat
docs: describe MCP setup
```

Commit **often** and in small chunks — the graders look for regular commits from
each member, not one giant dump at the end.

## 4. Open a Pull Request

```bash
git push -u origin feat/asr-whisper
```

Then open a PR on GitHub into `main`. Ask one teammate to review + approve before
merging. Don't merge your own PR without a review.

## 5. Ownership map

| Part | You implement | File(s) | Notes |
|------|---------------|---------|-------|
| 1 · ASR | `transcribe(audio, content_type) -> str` | `backend/app/asr.py` | Whisper / faster-whisper / parakeet |
| 2 · TTS | `synthesize(text, voice) -> bytes` (mp3) | `backend/app/tts.py` | ElevenLabs / XTTS / Fish Speech |
| 3 · Agent | *(done)* | `backend/app/agent.py`, `mcp_config.py` | add/adjust `TARGET_SITES` |
| 4 · Backend+Frontend | *(done)* | `backend/app/main.py`, `frontend/` | |

**The key rule:** parts 1 & 2 are just those two functions. Implement them and the
whole pipeline works — you don't touch anyone else's file.

## 6. Before you push

```bash
cd backend
uvicorn app.main:app --reload      # server starts without import errors
curl localhost:8000/api/health     # shows which parts are wired
```

## 7. Secrets

Never commit `.env` (it's gitignored). Copy `backend/.env.example` → `backend/.env`
and put your own keys there.
