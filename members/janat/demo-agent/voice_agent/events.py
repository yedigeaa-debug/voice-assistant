"""Event feed from sxodim.com (Kazakhstan's main going-out site).

The city pages are server-rendered; every event is an `.impression-card` with
clean data attributes -- no JS rendering needed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


@dataclass
class Event:
    title: str
    info: str        # "от 7000 тенге, 7 июля - 31 августа, Семейный курорт ..."
    category: str
    url: str
    min_price: str

    def spoken(self) -> str:
        """Short one-liner for speech: title + price/date, drop street addresses."""
        if not self.info:
            return self.title
        info = ", ".join(self.info.split(", ")[:2])  # keep price + date only
        return f"{self.title} — {info}"


# spoken-question keyword -> sxodim category substring (Russian site data)
CATEGORY_HINTS = {
    "концерт": "концерт", "concert": "концерт", "конц": "концерт",
    "театр": "театр", "theatre": "театр", "theater": "театр",
    "спектакл": "театр", "кино": "кино", "movie": "кино", "фильм": "кино",
    "выставк": "выставк", "exhibit": "выставк", "көрме": "выставк",
    "фестивал": "фестивал", "festival": "фестивал",
    "stand": "stand", "стендап": "stand", "лекц": "лекц",
}


def fetch_events(city: str = "almaty", timeout: float = 15.0) -> list[Event]:
    resp = requests.get(f"https://sxodim.com/{city}",
                        headers={"User-Agent": _UA}, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events, seen = [], set()
    for card in soup.select(".impression-card"):
        title = (card.get("data-title") or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)

        info_el = card.select_one(".impression-card-info")
        link_el = card.select_one("a.impression-card-title") or card.find("a")
        events.append(Event(
            title=title,
            info=re.sub(r"\s+", " ", info_el.get_text(" ", strip=True)) if info_el else "",
            category=(card.get("data-category") or "").strip(),
            url=(link_el.get("href") or "") if link_el else "",
            min_price=(card.get("data-minprice") or "").strip(),
        ))
    return events


def filter_events(events: list[Event], question: str, limit: int = 3) -> list[Event]:
    """Pick events matching a category hinted at in the question, else top-N."""
    q = question.lower()
    wanted = {cat for kw, cat in CATEGORY_HINTS.items() if kw in q}
    if wanted:
        matched = [e for e in events
                   if any(w in (e.category + " " + e.title).lower() for w in wanted)]
        if matched:
            return matched[:limit]
    return events[:limit]
