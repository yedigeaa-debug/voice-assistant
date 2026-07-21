"""Language identification for en / ru / kk from raw text.

Rule-based and dependency-free: Kazakh is Cyrillic-written like Russian, but
uses nine letters Russian doesn't have -- that's a perfect fingerprint.
"""

from __future__ import annotations

import re

# Letters unique to the Kazakh Cyrillic alphabet.
KK_LETTERS = set("әғқңөұүһіӘҒҚҢӨҰҮҺІ")

# Frequent Kazakh words that are written using only shared Cyrillic letters
# (needed when a short phrase happens to avoid Kazakh-specific letters).
# Only words that can't plausibly occur in a Russian sentence.
_KK_STOPWORDS = {
    "болады", "керек", "туралы", "немесе", "жатыр", "болып", "емес",
    "осында", "мынадай", "барамын", "айтшы",
}

_CYRILLIC_RE = re.compile(r"[а-яё]", re.IGNORECASE)
_LATIN_RE = re.compile(r"[a-z]", re.IGNORECASE)


def detect_language(text: str) -> str:
    """Return 'en', 'ru' or 'kk' for the given text."""
    if any(ch in KK_LETTERS for ch in text):
        return "kk"

    cyr = len(_CYRILLIC_RE.findall(text))
    lat = len(_LATIN_RE.findall(text))

    if cyr >= lat and cyr > 0:
        words = set(re.findall(r"[а-яё]+", text.lower()))
        if words & _KK_STOPWORDS:
            return "kk"
        return "ru"
    if lat > 0:
        return "en"
    return "en"  # nothing alphabetic -- safe default
