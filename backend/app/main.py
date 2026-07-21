"""
Part 4 — Backend orchestrator (FastAPI).

Wires the whole pipeline together:
    audio  --ASR-->  text  --Agent(+MCP)-->  answer  --TTS-->  audio

Endpoints:
    GET  /api/health       liveness + which parts are wired
    POST /api/chat         multipart audio upload -> ChatResponse (transcript,
                           answer, events, sources, base64 mp3)
    WS   /ws/asr           (bonus) real-time ASR — streams partial transcripts
    POST /api/tts/stream   (bonus) streaming TTS — mp3 chunks as they generate
"""

from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from . import asr, tts
from .agent import run_agent
from .realtime_asr import RealtimeASRUnavailable, StreamingTranscriber
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

    def realtime_asr_available() -> str:
        try:
            import faster_whisper  # noqa: F401
            return "available (faster-whisper installed)"
        except ImportError:
            return "install faster-whisper to enable"

    return {
        "status": "ok",
        "parts": {
            "asr (part 1)": wired(lambda: asr.transcribe(b"", content_type="audio/webm")),
            "agent+mcp (part 3)": "wired",
            "tts (part 2)": wired(lambda: tts.synthesize("")),
        },
        "bonus": {
            "realtime asr (/ws/asr)": realtime_asr_available(),
            "streaming tts (/api/tts/stream)": "endpoint ready; needs synthesize_stream()",
        },
    }


async def _answer(transcript: str) -> ChatResponse:
    """Agent (Part 3) + optional TTS (Part 2) for an already-transcribed request."""
    result = await run_agent(transcript)

    audio_b64: str | None = None
    try:
        audio_b64 = base64.b64encode(tts.synthesize(result.answer)).decode("ascii")
    except tts.TTSNotImplemented:
        audio_b64 = None

    return ChatResponse(
        transcript=transcript,
        answer=result.answer,
        events=result.events,
        sources=result.sources,
        audio_base64=audio_b64,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(audio: UploadFile = File(...)) -> ChatResponse:
    """Batch pipeline: audio -> ASR -> agent -> TTS."""
    raw = await audio.read()
    content_type = audio.content_type or "audio/webm"

    try:
        transcript = asr.transcribe(raw, content_type=content_type)
    except asr.ASRNotImplemented:
        transcript = ""

    if not transcript.strip():
        return ChatResponse(
            transcript="",
            answer="Я не расслышал(а) запрос. Похоже, модуль распознавания речи (Part 1) ещё не подключён.",
        )

    return await _answer(transcript)


@app.post("/api/agent", response_model=ChatResponse)
async def agent_from_text(payload: dict) -> ChatResponse:
    """
    Text-in pipeline used by real-time mode: the /ws/asr WebSocket already produced
    the transcript on the client, so we skip ASR and go straight to agent + TTS.
    POST {"text": "..."}.
    """
    transcript = (payload or {}).get("text", "").strip()
    if not transcript:
        return ChatResponse(transcript="", answer="Пустой запрос.")
    return await _answer(transcript)


@app.post("/api/transcribe")
async def transcribe_only(
    file: UploadFile = File(...),
    provider: str | None = Query(None, description="'local' or 'openai' (else from config)"),
    language: str | None = Query(None, description="ISO-639-1, e.g. 'ru'; empty = config"),
) -> dict:
    """
    Part 1 standalone endpoint (Dana): audio -> rich transcription result, no agent.
    Useful for testing ASR in isolation. Returns text + language + segments.
    """
    from .asr import get_asr
    from .config import ASR_LANGUAGE

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    try:
        provider_obj = get_asr(provider)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))

    suffix = Path(file.filename or "audio.webm").suffix.lower() or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(data)
        tmp.flush()
        result = provider_obj.transcribe(tmp.name, language=language or ASR_LANGUAGE)
    return result.to_dict()


@app.websocket("/ws/asr")
async def ws_asr(ws: WebSocket) -> None:
    """
    Bonus (real-time ASR). Protocol:
      client -> server : binary frames = 16-bit mono PCM @ 16 kHz (mic audio),
                         then a text frame "__END__" when the user stops talking.
      server -> client : {"partial": "..."} live as speech comes in,
                         {"final": "...", "done": true} once, at the end,
                         {"error": "..."} if the local model isn't available.

    Runs faster-whisper-small locally (see realtime_asr.py). The transcription is
    blocking, so it's offloaded to a thread to keep the event loop responsive.
    """
    import asyncio

    await ws.accept()
    try:
        transcriber = StreamingTranscriber(language="ru")
    except RealtimeASRUnavailable as e:
        await ws.send_json({"error": str(e)})
        await ws.close()
        return

    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                return
            if (data := msg.get("bytes")) is not None:
                partial = await asyncio.to_thread(transcriber.feed, data)
                if partial:
                    await ws.send_json({"partial": partial})
            elif msg.get("text") == "__END__":
                final = await asyncio.to_thread(transcriber.final)
                await ws.send_json({"final": final, "done": True})
                return
    except WebSocketDisconnect:
        return


@app.post("/api/tts/stream")
async def tts_stream(payload: dict) -> StreamingResponse:
    """
    Bonus (streaming TTS): POST {"text": "...", "voice": "..."} and get mp3 back as
    a chunked stream, so playback can start before synthesis finishes.
    """
    text = (payload or {}).get("text", "")
    voice = (payload or {}).get("voice")

    async def gen():
        try:
            async for chunk in tts.synthesize_stream(text, voice=voice):
                yield chunk
        except tts.TTSNotImplemented:
            return  # empty stream; frontend shows text-only fallback

    return StreamingResponse(gen(), media_type="audio/mpeg")


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": str(exc)})
