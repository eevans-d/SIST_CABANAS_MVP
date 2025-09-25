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

    matches = DATE_PATTERN.findall(text)
    results = []
    for m, _ in matches:
        parsed = dateparse(m, settings={'DATE_ORDER': 'DMY'})
        if parsed:
            results.append(parsed.date().isoformat())
    return {"dates": results}


def analyze(text: str) -> Dict[str, Any]:
    r = {}
    r.update(detect_intent(text))
    r.update(extract_dates(text))
    return r
