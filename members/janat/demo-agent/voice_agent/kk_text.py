"""Kazakh text frontend for XTTS-v2.

XTTS-v2 does not support Kazakh, but Kazakh is written in Cyrillic and its
phoneme inventory is close enough to Russian that a careful grapheme mapping,
spoken by the Russian branch of the model, sounds natural:

  * і -> и, ұ -> у, қ -> к, ғ -> г, ң -> н, һ -> х   (plain substitutions)
  * ә/ө/ү after a consonant -> я/ё/ю                 (Russian iotated vowels
    palatalize the consonant, which fronts the vowel -- acoustically much
    closer to the Kazakh front vowels than plain а/о/у)
  * ә/ө/ү elsewhere -> а/о/у

Numbers are expanded to Kazakh words *before* the mapping (the model's own
num2words would read them in Russian otherwise).
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------- numbers ---

_UNITS = ["нөл", "бір", "екі", "үш", "төрт", "бес", "алты", "жеті", "сегіз", "тоғыз"]
_TENS = ["", "он", "жиырма", "отыз", "қырық", "елу", "алпыс", "жетпіс", "сексен", "тоқсан"]
_SCALES = [(10**9, "миллиард"), (10**6, "миллион"), (10**3, "мың")]


def num_to_words_kk(n: int) -> str:
    """Integer -> Kazakh words. Kazakh numerals are pleasantly regular."""
    if n < 0:
        return "минус " + num_to_words_kk(-n)
    if n < 10:
        return _UNITS[n]

    parts: list[str] = []
    for scale, name in _SCALES:
        if n >= scale:
            head, n = divmod(n, scale)
            # "бір мың" -> just "мың"
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


def _expand_numbers(text: str) -> str:
    # "7 000" / "7,000" style thousand groups first
    text = re.sub(r"(?<=\d)[ ,](?=\d{3}\b)", "", text)
    return re.sub(r"\d+", lambda m: num_to_words_kk(int(m.group())), text)


# ----------------------------------------------------- phonetic mapping ----

_PLAIN = str.maketrans("іұқғңһІҰҚҒҢҺ", "иукгнхИУКГНХ")

# vowels that get an iotated variant after a consonant
_IOTATED = {"ә": ("я", "а"), "ө": ("ё", "о"), "ү": ("ю", "у"),
            "Ә": ("Я", "А"), "Ө": ("Ё", "О"), "Ү": ("Ю", "У")}

_CONSONANTS = set("бвгғджзйкқлмнңпрстфхһцчшщБВГҒДЖЗЙКҚЛМНҢПРСТФХҺЦЧШЩ")


def kazakh_to_russian_graphemes(text: str) -> str:
    """Map Kazakh Cyrillic onto Russian graphemes for the XTTS 'ru' voice."""
    out: list[str] = []
    prev = ""
    for ch in text:
        if ch in _IOTATED:
            soft, hard = _IOTATED[ch]
            out.append(soft if prev in _CONSONANTS else hard)
        else:
            out.append(ch)
        prev = ch
    return "".join(out).translate(_PLAIN)


def prepare_kazakh(text: str) -> str:
    """Full Kazakh pipeline: expand numbers, then map to Russian graphemes."""
    return kazakh_to_russian_graphemes(_expand_numbers(text))


# --------------------------------------------- Cyrillic -> Latin (for en) ---

_RU_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ә": "a", "ғ": "g", "қ": "k", "ң": "n", "ө": "o", "ұ": "u", "ү": "u",
    "һ": "h", "і": "i",
}


def cyrillic_to_latin(text: str) -> str:
    """Transliterate Cyrillic so the English XTTS voice can read event names."""
    out = []
    for ch in text:
        lower = ch.lower()
        if lower in _RU_LAT:
            lat = _RU_LAT[lower]
            out.append(lat.capitalize() if ch.isupper() and lat else lat)
        else:
            out.append(ch)
    return "".join(out)
