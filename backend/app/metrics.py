from __future__ import annotations

from prometheus_client import Counter, Gauge

# Contadores/Métricas centralizados para evitar registros duplicados en el registry

NLU_PRE_RESERVE = Counter(
    "nlu_pre_reserve_total",
    "Acciones NLU hacia pre-reserva",
    ["action", "source"],
)

ICAL_LAST_SYNC_AGE_MIN = Gauge(
    "ical_last_sync_age_minutes",
    "Minutos desde la última sincronización iCal más reciente",
)
