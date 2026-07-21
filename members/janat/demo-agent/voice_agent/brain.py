"""Turns a user question into a natural spoken-style answer in en / ru / kk.

Two modes:
  * If ANTHROPIC_API_KEY is set (and `anthropic` installed), Claude writes a
    conversational answer grounded in the scraped events.
  * Otherwise a careful template fallback -- still fluent, fully offline.
"""

from __future__ import annotations

import os

from .events import Event, fetch_events, filter_events
from .kk_text import cyrillic_to_latin

_EVENT_TRIGGERS = (
    # en
    "event", "happening", "going on", "concert", "what to do", "where to go",
    "things to do", "show", "exhibit", "festival",
    # ru
    "событ", "мероприят", "куда сходить", "что посмотреть", "происходит",
    "концерт", "интересного", "чем занят", "выставк", "спектакл", "афиш",
    # kk
    "іс-шара", "не өтіп жатыр", "қайда бар", "не істе", "қызық", "оқиға",
    "шара", "концерт",
)

_INTRO = {
    "en": "Here's what's on in Almaty right now.",
    "ru": "Вот что интересного сейчас проходит в Алматы.",
    "kk": "Алматыда қазір өтіп жатқан қызықты іс-шаралар мыналар.",
}
_OUTRO = {
    "en": "Want details on any of these?",
    "ru": "Рассказать подробнее о чём-нибудь из этого?",
    "kk": "Осылардың бірі туралы толығырақ айтайын ба?",
}
_EMPTY = {
    "en": "Sorry, I couldn't reach the events site right now. Please try again later.",
    "ru": "К сожалению, не получилось загрузить афишу. Попробуйте ещё раз чуть позже.",
    "kk": "Өкінішке қарай, афишаны жүктеу мүмкін болмады. Сәл кейінірек қайталап көріңіз.",
}
_SMALLTALK = {
    "en": "I'm your Almaty guide. Ask me what's happening in the city — "
          "concerts, theatre, exhibitions — in English, Russian or Kazakh.",
    "ru": "Я ваш гид по Алматы. Спросите, что происходит в городе — "
          "концерты, театр, выставки — на русском, казахском или английском.",
    "kk": "Мен Алматы бойынша гидпін. Қалада не өтіп жатқанын сұраңыз — "
          "концерттер, театр, көрмелер — қазақша, орысша немесе ағылшынша.",
}


def answer(question: str, language: str, city: str = "almaty") -> str:
    """Compose the agent's reply text in the user's language."""
    if not _is_events_question(question):
        return _SMALLTALK[language]

    try:
        events = filter_events(fetch_events(city), question)
    except Exception:
        events = []
    if not events:
        return _EMPTY[language]

    llm = _llm_answer(question, language, events)
    return llm if llm else _template_answer(language, events)


def _is_events_question(question: str) -> bool:
    q = question.lower()
    return any(t in q for t in _EVENT_TRIGGERS)


# ------------------------------------------------------------- template ----

def _template_answer(language: str, events: list[Event]) -> str:
    lines = []
    for e in events:
        line = e.spoken()
        if language == "en":
            # English XTTS voice can't read Cyrillic -- transliterate.
            line = cyrillic_to_latin(line.replace("тенге", "tenge")
                                     .replace("теңге", "tenge"))
        lines.append(line + ".")
    return " ".join([_INTRO[language], *lines, _OUTRO[language]])


# ------------------------------------------------------------ LLM polish ---

_LANG_NAME = {"en": "English", "ru": "Russian", "kk": "Kazakh"}


def _llm_answer(question: str, language: str, events: list[Event]) -> str | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    listing = "\n".join(f"- {e.title} | {e.info} | category: {e.category}"
                        for e in events)
    prompt = (
        f"You are a friendly local guide in Almaty. The user asked (voice):\n"
        f"{question!r}\n\nCurrent events from sxodim.com:\n{listing}\n\n"
        f"Answer in {_LANG_NAME[language]}, 3-5 short sentences, natural "
        f"SPOKEN style (the reply will be synthesized as audio): no lists, no "
        f"markdown, no URLs. Mention 2-3 of the most fitting events with "
        f"their dates/prices woven into sentences."
        + (" Write event titles in Latin transliteration."
           if language == "en" else "")
    )
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return None  # network/quota problems -> template fallback
