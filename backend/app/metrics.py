"""Métricas centralizadas de Prometheus para el sistema."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# Contadores/Métricas centralizados para evitar registros duplicados en el registry

# NLU Metrics
NLU_PRE_RESERVE = Counter(
    "nlu_pre_reserve_total",
    "Acciones NLU hacia pre-reserva",
    ["action", "source"],
)

# Background Jobs Metrics
PRERESERVATIONS_EXPIRED = Counter(
    "prereservations_expired_total",
    "Total de pre-reservas expiradas por job",
    ["accommodation_id"],
)

PRERESERVATION_EXPIRY_DURATION = Histogram(
    "prereservation_expiry_job_duration_seconds",
    "Duración del job de expiración de pre-reservas",
)

PRERESERVATION_REMINDERS_SENT = Counter(
    "prereservation_reminders_sent_total",
    "Total de recordatorios de pre-reserva enviados",
    ["channel"],
)

# iCal Sync Metrics
ICAL_LAST_SYNC_AGE_MIN = Gauge(
    "ical_last_sync_age_minutes",
    "Minutos desde la última sincronización iCal más reciente",
)

ICAL_SYNC_AGE_MINUTES = Gauge(
    "ical_sync_age_minutes",
    "Minutos desde última sync iCal por alojamiento",
    ["accommodation_id"],
)

ICAL_SYNC_ERRORS = Counter(
    "ical_sync_errors_total",
    "Errores de sincronización iCal",
    ["accommodation_id", "error_type"],
)

ICAL_SYNC_DURATION = Histogram(
    "ical_sync_job_duration_seconds",
    "Duración del job de sincronización iCal",
)

ICAL_EVENTS_IMPORTED = Counter(
    "ical_events_imported_total",
    "Total de eventos iCal importados",
    ["accommodation_id", "source"],
)

# ============================================================================
# MÉTRICAS DE RATE LIMITING (Fase 4.3)
# ============================================================================

RATE_LIMIT_BLOCKED = Counter(
    "rate_limit_requests_blocked_total",
    "Requests bloqueados por rate limiting",
    ["path", "client_ip"],
)

RATE_LIMIT_CURRENT_COUNT = Gauge(
    "rate_limit_current_count",
    "Contador actual de requests en ventana de rate limit",
    ["client_ip", "path"],
)

RATE_LIMIT_REDIS_ERRORS = Counter(
    "rate_limit_redis_errors_total",
    "Errores de Redis durante rate limiting (fail-open)",
)
