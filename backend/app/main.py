"""FastAPI-бэкенд голосового ассистента.

Часть 1 (ASR): принимаем аудио от пользователя и возвращаем текст.
Следующие части добавят агента (LangChain + MCP Playwright) и TTS.
"""
import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .asr import get_asr
from .config import ASR_LANGUAGE, ASR_PROVIDER, MAX_AUDIO_BYTES

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Voice Leisure Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # на проде сузить до адреса фронтенда
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg"}


@app.get("/api/health")
def health():
    return {"status": "ok", "asr_provider": ASR_PROVIDER}


@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    provider: str | None = Query(None, description="'local' или 'openai' (иначе — из конфига)"),
    language: str | None = Query(None, description="ISO-639-1, напр. 'ru'; пусто = из конфига"),
):
    suffix = Path(file.filename or "audio.webm").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, f"Неподдерживаемый формат {suffix}. Допустимы: {sorted(ALLOWED_EXTENSIONS)}")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Пустой файл")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Файл больше 25 MB — запишите короче или нарежьте на чанки")

    try:
        asr = get_asr(provider)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        result = asr.transcribe(tmp.name, language=language or ASR_LANGUAGE)

    return result.to_dict()
