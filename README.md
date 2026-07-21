# 🎙️ Voice AI Assistant with Web Search

A full voice AI assistant for leisure planning. You talk to it, it browses real event
websites (sxodim.com, kino.kz, ticketon.kz) using **MCP Playwright**, and it answers
you back in voice.

**Pipeline:** `Voice In → ASR → LangChain Agent + MCP Playwright → TTS → Voice Out`

```
 Frontend (UI)              Backend (Server)                 External (Web)
 ┌──────────┐   audio   ┌─────────────────────┐   MCP    ┌──────────────┐
 │  🎤 Mic  │─────────▶ │  ASR (Whisper)      │          │  sxodim.com  │
 └──────────┘           │        │            │          │  ticketon.kz │
      ▲                 │        ▼            │◀────────▶│  kino.kz     │
 ┌──────────┐   audio   │  LangChain Agent    │  events  └──────────────┘
 │ 🔊 Speaker│◀──────── │  + LLM  →  TTS      │
 └──────────┘           └─────────────────────┘
```

## 📦 Repository layout (monorepo)

```
voice-assistant/
├── backend/          # Part 3 (agent) + Part 4 (server) — FastAPI + LangChain + MCP
│   ├── app/
│   │   ├── main.py           # FastAPI app, /api/chat endpoint (orchestrator)
│   │   ├── agent.py          # Part 3: LangChain agent + MCP Playwright
│   │   ├── mcp_config.py     # MCP Playwright server config + target sites
│   │   ├── asr.py            # Part 1 interface (teammate plugs in Whisper etc.)
│   │   ├── tts.py            # Part 2 interface (teammate plugs in ElevenLabs etc.)
│   │   └── schemas.py        # Pydantic request/response models
│   ├── requirements.txt
│   └── .env.example
├── frontend/         # Part 4: minimal UI — record button, thinking animation, playback
│   └── index.html
├── docs/
│   └── ARCHITECTURE.md
├── CONTRIBUTING.md   # Git workflow for the team (branches, PRs)
└── README.md
```

## 👥 Who owns what

| Part | Component | Folder / file | Owner |
|------|-----------|---------------|-------|
| 1 | ASR (Speech→Text) | `backend/app/asr.py` | _teammate_ |
| 2 | TTS (Text→Speech) | `backend/app/tts.py` | _teammate_ |
| **3** | **LangChain Agent + MCP Playwright** | `backend/app/agent.py`, `mcp_config.py` | **you (yedigeaa-debug)** |
| **4** | **Backend orchestration + Frontend** | `backend/app/main.py`, `frontend/` | **you (yedigeaa-debug)** |

Parts 1 & 2 are wired as **clean interfaces** — teammates implement the two functions in
`asr.py` / `tts.py` and the whole pipeline works, no other file needs to change.

## 🚀 Quick start

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # fill in OPENAI_API_KEY etc.

# 2. MCP Playwright server needs Node + the Playwright MCP package (installed on demand via npx)
#    First run will download Chromium.
npx -y @playwright/mcp@latest --version   # optional: warm the cache

# 3. Run the server
uvicorn app.main:app --reload --port 8000

# 4. Frontend — just open it (talks to http://localhost:8000)
open ../frontend/index.html          # or serve it: python -m http.server 5500
```

## ✅ Definition of Done (from the spec)

- [ ] End-to-end voice flow works (ask by voice, get voice answer)
- [ ] MCP Playwright integrated — agent surfs target sites for real events
- [ ] Decent ASR + quality TTS voice
- [ ] Code organized — backend/frontend split, logical API
- [ ] Team uses Git (branches, PRs, regular commits from everyone)

## 🌟 Bonus (Advanced / real-time)

- Real-time ASR over WebSocket (`faster-whisper-small`) — stub endpoint `/ws/asr` is scaffolded
- Streaming TTS back to the frontend — see `docs/ARCHITECTURE.md`
