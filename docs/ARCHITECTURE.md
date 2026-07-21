# Architecture

## Pipeline

```
Browser (frontend/index.html)
   │  POST /api/chat  (multipart: audio blob, webm/opus)
   ▼
FastAPI  backend/app/main.py
   │  1. asr.transcribe(audio) ─────────────▶ text          (Part 1, teammate)
   │  2. agent.run_agent(text) ──────────────▶ AgentResult   (Part 3)
   │        └─ LangGraph ReAct agent + ChatOpenAI
   │           └─ Playwright MCP tools (navigate / read / click)
   │              └─ sxodim.com · ticketon.kz · kino.kz
   │  3. tts.synthesize(answer) ─────────────▶ mp3 bytes      (Part 2, teammate)
   ▼
ChatResponse { transcript, answer, events[], sources[], audio_base64 }
   │  played + rendered in the browser
   ▼
Speaker + chat UI
```

## Module boundaries (why this split)

- **`asr.py` / `tts.py`** expose exactly one function each. The orchestrator only
  knows those signatures, so teammates own their model choices without merge
  conflicts. If a stub isn't implemented yet, the pipeline degrades gracefully:
  no ASR → friendly "не расслышал" reply; no TTS → text-only answer.
- **`agent.py`** is the only place that talks to the LLM and to MCP. It returns a
  typed `AgentResult`, so the backend never parses LLM text.
- **`mcp_config.py`** isolates *what sites* and *how to launch the MCP server* from
  *agent logic*. Editing target sites = editing one list.

## MCP Playwright

We use `@playwright/mcp` launched over stdio (`npx -y @playwright/mcp@latest
--headless`). `langchain-mcp-adapters` turns its tools (browser navigate, snapshot,
click, type, …) into LangChain tools the ReAct agent can call autonomously. The
agent decides which site to visit from the system prompt's site catalog.

Requirements: Node.js (for `npx`) and Chromium (downloaded on first run).

## Bonus: real-time (advanced level) — implemented

### 1. Real-time ASR over WebSocket

```
Browser                                  Backend  (WS /ws/asr)
  AudioWorklet: mic -> 16kHz mono PCM16
  ── binary PCM frames ───────────────▶  StreamingTranscriber.feed()
                                           (faster-whisper-small, rolling buffer)
  ◀── {"partial": "..."} every ~0.7s ──   re-transcribe on new audio
  ── text "__END__" (user stopped) ────▶  StreamingTranscriber.final()
  ◀── {"final": "...", "done": true} ──
  then POST /api/agent {text} ─────────▶  agent (skips ASR) -> answer
```

Files: `backend/app/realtime_asr.py` (model + buffering), `main.py` (`/ws/asr`,
`/api/agent`), `frontend/index.html` (AudioWorklet + WS client, live caret UI).
Blocking transcription runs in `asyncio.to_thread` so the event loop stays free.
If `faster-whisper` isn't installed, the socket returns a clear `{"error": ...}`.

### 2. Streaming TTS

```
Browser                          Backend (POST /api/tts/stream)
  fetch(text) ─────────────────▶ tts.synthesize_stream(text)  (async generator)
  MediaSource.appendBuffer  ◀─── StreamingResponse: mp3 chunks as generated
  playback starts on 1st chunk
```

`tts.py::synthesize_stream` ships with a commented ElevenLabs streaming reference;
until Janat wires a provider it falls back to yielding the batch `synthesize()`
result as one chunk, so the endpoint always works. Swap in XTTS-v2 / Fish Speech
streaming the same way. Combining this with agent token streaming would cut
perceived latency further (future work).
