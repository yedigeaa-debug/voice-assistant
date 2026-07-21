# 🎙 Голосовой AI-ассистент по планированию досуга

Групповой проект семинара. Реализация по частям:

- **Часть 1 — ASR (Speech-to-Text)** ✅ (этот этап)
- Часть 2 — TTS (Text-to-Speech) — TODO
- Часть 3 — LangChain-агент + MCP Playwright — TODO
- Часть 4 — Frontend — TODO

## Часть 1: Распознавание речи

Два взаимозаменяемых провайдера за общим интерфейсом (`backend/app/asr/`):

| Провайдер | Модель | Когда использовать |
|-----------|--------|--------------------|
| `local` (по умолчанию) | `Systran/faster-whisper-small` (CTranslate2) | Бесплатно, офлайн, быстро даже на CPU; подходит для realtime-бонуса |
| `openai` | `gpt-4o-mini-transcribe` (рекомендация июля 2026; `whisper-1` — legacy) | Максимальное качество без GPU |

Гиперпараметры выставлены по подсказкам семинара:
`beam_size=5`, `temperature=[0.0, 0.2, 0.4]` (fallback против галлюцинаций),
`condition_on_previous_text=False` (защита от «залипания»), VAD-фильтр тишины,
доменный `prompt` с терминами афиши для облачной модели.

## Запуск

```bash
cd voice-assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env   # при необходимости впишите OPENAI_API_KEY

cd backend
uvicorn app.main:app --reload --port 8000
```

## API

- `GET /api/health` — статус и активный провайдер.
- `POST /api/transcribe` — multipart-файл `file` (mp3/wav/webm/m4a/ogg…, до 25 MB).
  Query-параметры: `provider=local|openai`, `language=ru|en|...`.

Пример:

```bash
curl -s -X POST "http://localhost:8000/api/transcribe?provider=local" \
  -F "file=@tests/audio/sample_ru.wav" | python3 -m json.tool
```

Ответ:

```json
{
  "text": "Привет! Куда можно сходить сегодня вечером в Алматы?",
  "language": "ru",
  "duration": 4.6,
  "provider": "local",
  "model": "faster-whisper-small",
  "segments": [{"start": 0.0, "end": 4.6, "text": "..."}]
}
```

## Структура

```
voice-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI: /api/health, /api/transcribe
│   │   ├── config.py          # настройки из .env
│   │   └── asr/
│   │       ├── base.py        # интерфейс ASRProvider + TranscriptionResult
│   │       ├── local_whisper.py   # faster-whisper (локально)
│   │       └── openai_whisper.py  # OpenAI Audio API (облако)
│   ├── tests/audio/           # тестовые сэмплы
│   ├── requirements.txt
│   └── .env.example
└── README.md
```
