"""Конфигурация ASR-модуля (Часть 1 проекта)."""
import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Провайдер по умолчанию: "local" (faster-whisper) или "openai" (облако)
ASR_PROVIDER = os.getenv("ASR_PROVIDER", "local")

# --- Облачный ASR ---
# whisper-1 помечен как legacy (июль 2026);
# рекомендованная модель — gpt-4o-mini-transcribe (~$0.003/мин, меньше галлюцинаций)
OPENAI_ASR_MODEL = os.getenv("OPENAI_ASR_MODEL", "gpt-4o-mini-transcribe")

# --- Локальный ASR ---
# Systran/faster-whisper-small: CTranslate2-имплементация, быстрая и лёгкая —
# именно её семинар рекомендует для realtime-сценария
LOCAL_ASR_MODEL = os.getenv("LOCAL_ASR_MODEL", "small")
LOCAL_ASR_DEVICE = os.getenv("LOCAL_ASR_DEVICE", "auto")  # auto / cpu / cuda
LOCAL_ASR_COMPUTE = os.getenv("LOCAL_ASR_COMPUTE", "int8")  # int8 на CPU, float16 на GPU

# Язык по умолчанию (явное указание ускоряет и повышает точность);
# None = автоопределение
ASR_LANGUAGE = os.getenv("ASR_LANGUAGE", "ru") or None

# Максимальный размер загружаемого аудио (лимит OpenAI API — 25 MB)
MAX_AUDIO_BYTES = 25 * 1024 * 1024
