"""Text frontend for Part 2 TTS: language ID, Kazakh bridge, chunking.

XTTS-v2 supports en/ru (and 15 more) but NOT Kazakh. Kazakh is made to work
through a phonetic bridge: numbers are expanded with a tiny Kazakh num2words,
then Kazakh-only letters are mapped to their closest Russian graphemes and the
result is spoken by the model's Russian voice. Details in members/janat.
"""

from __future__ import annotations

import re

# ------------------------------------------------------------ language ID --

KK_LETTERS = set("әғқңөұүһіӘҒҚҢӨҰҮҺІ")
_KK_STOPWORDS = {  # Kazakh words spelled with shared-Cyrillic letters only
    "болады", "керек", "туралы", "немесе", "жатыр", "болып", "емес",
    "осында", "мынадай", "барамын", "айтшы",
}
_CYR = re.compile(r"[а-яё]", re.IGNORECASE)
_LAT = re.compile(r"[a-z]", re.IGNORECASE)


def detect_language(text: str) -> str:
    """Return 'en', 'ru' or 'kk'."""
    if any(ch in KK_LETTERS for ch in text):
        return "kk"
    cyr, lat = len(_CYR.findall(text)), len(_LAT.findall(text))
    if cyr >= lat and cyr > 0:
        if set(re.findall(r"[а-яё]+", text.lower())) & _KK_STOPWORDS:
            return "kk"
        return "ru"
    return "en"


# ------------------------------------------------------- Kazakh -> Russian --

_UNITS = ["нөл", "бір", "екі", "үш", "төрт", "бес", "алты", "жеті", "сегіз", "тоғыз"]
_TENS = ["", "он", "жиырма", "отыз", "қырық", "елу", "алпыс", "жетпіс", "сексен", "тоқсан"]
_SCALES = [(10**9, "миллиард"), (10**6, "миллион"), (10**3, "мың")]


def num_to_words_kk(n: int) -> str:
    if n < 0:
        return "минус " + num_to_words_kk(-n)
    if n < 10:
        return _UNITS[n]
    parts: list[str] = []
    for scale, name in _SCALES:
        if n >= scale:
            head, n = divmod(n, scale)
            parts.append((num_to_words_kk(head) + " " if head > 1 else "") + name)
    if n >= 100:
        head, n = divmod(n, 100)
        parts.append((_UNITS[head] + " " if head > 1 else "") + "жүз")
    if n >= 10:
        head, n = divmod(n, 10)
        parts.append(_TENS[head])
    if n > 0:
        parts.append(_UNITS[n])
    return " ".join(parts)


_PLAIN = str.maketrans("іұқғңһІҰҚҒҢҺ", "иукгнхИУКГНХ")
_IOTATED = {"ә": ("я", "а"), "ө": ("ё", "о"), "ү": ("ю", "у"),
            "Ә": ("Я", "А"), "Ө": ("Ё", "О"), "Ү": ("Ю", "У")}
_CONSONANTS = set("бвгғджзйкқлмнңпрстфхһцчшщБВГҒДЖЗЙКҚЛМНҢПРСТФХҺЦЧШЩ")


def prepare_kazakh(text: str) -> str:
    """Kazakh text -> Russian graphemes the XTTS 'ru' voice pronounces well."""
    text = re.sub(r"(?<=\d)[ ,](?=\d{3}\b)", "", text)          # 7 000 -> 7000
    text = re.sub(r"\d+", lambda m: num_to_words_kk(int(m.group())), text)
    out, prev = [], ""
    for ch in text:
        if ch in _IOTATED:
            soft, hard = _IOTATED[ch]
            out.append(soft if prev in _CONSONANTS else hard)
        else:
            out.append(ch)
        prev = ch
    return "".join(out).translate(_PLAIN)


# ------------------------------------------------------------- chunking ----

_SENT_RE = re.compile(r"(?<=[.!?…])\s+")


def chunk_text(text: str, limit: int) -> list[str]:
    """Sentence-aware split into <=limit pieces (XTTS rushes long inputs)."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if text[-1] not in ".!?…":
        text += "."
    chunks, buf = [], ""
    for sent in _SENT_RE.split(text):
        for piece in _split_long(sent, limit):
            if buf and len(buf) + len(piece) + 1 <= limit:
                buf += " " + piece
            else:
                if buf:
                    chunks.append(buf)
                buf = piece
    if buf:
        chunks.append(buf)
    return chunks


def _split_long(sent: str, limit: int) -> list[str]:
    if len(sent) <= limit:
        return [sent]
    parts, buf = [], ""
    for frag in re.split(r"(?<=,)\s+", sent):
        while len(frag) > limit:
            cut = frag.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            parts.append(frag[:cut])
            frag = frag[cut:].strip()
        if buf and len(buf) + len(frag) + 1 <= limit:
            buf += " " + frag
        else:
            if buf:
                parts.append(buf)
            buf = frag
    if buf:
        parts.append(buf)
    return parts
