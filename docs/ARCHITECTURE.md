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

## Bonus: real-time (advanced level)

**Real-time ASR (WebSocket).** Endpoint `WS /ws/asr` is scaffolded in `main.py`.
The frontend would stream audio chunks (from `MediaRecorder` with a small
`timeslice`) while the user is still speaking; the ASR teammate plugs a streaming
recognizer (e.g. `faster-whisper-small`) at the marked spot and pushes partial
transcripts back with `ws.send_json({"partial": ...})`. The UI shows text live.

**Streaming TTS.** Add `synthesize_stream(text) -> AsyncIterator[bytes]` in
`tts.py` (ElevenLabs streaming API or a local XTTS-v2 / Fish Speech stream) and a
`StreamingResponse` endpoint so audio starts playing before the full answer is
generated. Combine with the agent streaming tokens for lowest perceived latency.
