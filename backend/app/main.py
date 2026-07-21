"""
Part 4 — Backend orchestrator (FastAPI).

Wires the whole pipeline together:
    audio  --ASR-->  text  --Agent(+MCP)-->  answer  --TTS-->  audio

Endpoints:
    GET  /api/health   liveness + which parts are wired
    POST /api/chat     multipart audio upload -> ChatResponse (transcript, answer,
                       events, sources, base64 mp3)
    WS   /ws/asr       (bonus) real-time ASR stub — see docstring
"""

from __future__ import annotations

import base64
import os

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import asr, tts
from .agent import run_agent
from .schemas import ChatResponse

app = FastAPI(title="Voice AI Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    def wired(check) -> str:
        try:
            check()
        except (asr.ASRNotImplemented, tts.TTSNotImplemented):
            return "stub — teammate needs to implement it"
        except Exception:
            return "wired"
        return "wired"

    return {
        "status": "ok",
        "parts": {
            "asr (part 1)": wired(lambda: asr.transcribe(b"", content_type="audio/webm")),
            "agent+mcp (part 3)": "wired",
            "tts (part 2)": wired(lambda: tts.synthesize("")),
        },
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(audio: UploadFile = File(...)) -> ChatResponse:
    raw = await audio.read()
    content_type = audio.content_type or "audio/webm"

    # 1) ASR (Part 1)
    try:
        transcript = asr.transcribe(raw, content_type=content_type)
    except asr.ASRNotImplemented:
        transcript = ""

    if not transcript.strip():
        return ChatResponse(
            transcript="",
            answer="Я не расслышал(а) запрос. Похоже, модуль распознавания речи (Part 1) ещё не подключён.",
            events=[],
            sources=[],
            audio_base64=None,
        )

    # 2) Agent + MCP Playwright (Part 3)
    result = await run_agent(transcript)

    # 3) TTS (Part 2) — optional; pipeline still returns text if not wired
    audio_b64: str | None = None
    try:
        mp3 = tts.synthesize(result.answer)
        audio_b64 = base64.b64encode(mp3).decode("ascii")
    except tts.TTSNotImplemented:
        audio_b64 = None

    return ChatResponse(
        transcript=transcript,
        answer=result.answer,
        events=result.events,
        sources=result.sources,
        audio_base64=audio_b64,
    )


@app.websocket("/ws/asr")
async def ws_asr(ws: WebSocket) -> None:
    """
    Bonus (real-time ASR): the frontend streams audio chunks here while the user
    is still speaking; the server transcribes incrementally and pushes partial
    text back. This stub just echoes chunk sizes — the ASR teammate plugs a
    streaming model (e.g. faster-whisper-small) into the marked spot.
    """
    await ws.accept()
    try:
        while True:
            chunk = await ws.receive_bytes()
            # >>> ASR teammate: feed `chunk` to a streaming recognizer and send
            #     back partial transcripts, e.g. await ws.send_json({"partial": ...})
            await ws.send_json({"partial": "", "bytes_received": len(chunk)})
    except WebSocketDisconnect:
        return


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": str(exc)})
