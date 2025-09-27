import re
from datetime import date
from typing import Dict, Any, Optional
from dateparser import parse as dateparse
from app.utils.datetime_utils import get_next_weekend

INTENT_KEYWORDS = {
    "disponibilidad": re.compile(r"disponib|libre|hay", re.IGNORECASE),
    "precio": re.compile(r"precio|costo|sale|cuanto", re.IGNORECASE),
    "reservar": re.compile(r"reserv|apart|tomo", re.IGNORECASE),
    "servicios": re.compile(r"servicio|incluye|wifi", re.IGNORECASE),
}

DATE_PATTERN = re.compile(r"(\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?)")
WEEKEND_PATTERN = re.compile(r"fin de semana|finde", re.IGNORECASE)
RANGE_PATTERN = re.compile(
    r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\s*(?:al|-|a)\s*(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)",
    re.IGNORECASE,
)
GUESTS_PATTERN = re.compile(r"(\d+)\s*(personas?|pax|hu[eé]spedes?)", re.IGNORECASE)


def detect_intent(text: str) -> Dict[str, Any]:
    intents = []
    for name, pattern in INTENT_KEYWORDS.items():
        if pattern.search(text):
            intents.append(name)
    return {"intents": intents or ["desconocido"]}


def extract_dates(text: str) -> Dict[str, Any]:
    # weekend shortcut
    if WEEKEND_PATTERN.search(text):
        sat, sun = get_next_weekend()
        return {"dates": [sat.isoformat(), sun.isoformat()]}

    # explicit range like "15/12 al 18/12"
    m = RANGE_PATTERN.search(text)
    if m:
        d1_raw, d2_raw = m.group(1), m.group(2)
        d1 = dateparse(d1_raw, settings={'DATE_ORDER': 'DMY'})
        d2 = dateparse(d2_raw, settings={'DATE_ORDER': 'DMY'})
        results = []
        if d1:
            results.append(d1.date().isoformat())
        if d2:
            results.append(d2.date().isoformat())
        if results:
            return {"dates": results}

    matches = DATE_PATTERN.findall(text)
    results = []
    for m, _ in matches:
        parsed = dateparse(m, settings={'DATE_ORDER': 'DMY'})
        if parsed:
            results.append(parsed.date().isoformat())
    return {"dates": results}


def extract_guests(text: str) -> Dict[str, Any]:
    m = GUESTS_PATTERN.search(text)
    if m:
        try:
            return {"guests": int(m.group(1))}
        except Exception:
            return {}
    return {}


def analyze(text: str) -> Dict[str, Any]:
    r = {}
    r.update(detect_intent(text))
    r.update(extract_dates(text))
    guests = extract_guests(text)
    if guests:
        r.update(guests)
    return r
