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

# ============================================================================
# MÉTRICAS DE IDEMPOTENCIA (Fase 6.2)
# ============================================================================

IDEMPOTENCY_CACHE_HITS = Counter(
    "idempotency_cache_hits_total",
    "Requests respondidos desde caché de idempotencia",
    ["endpoint", "method"],
)

IDEMPOTENCY_CACHE_MISSES = Counter(
    "idempotency_cache_misses_total",
    "Requests procesados (no encontrados en caché)",
    ["endpoint", "method"],
)

IDEMPOTENCY_KEYS_CREATED = Counter(
    "idempotency_keys_created_total",
    "Claves de idempotencia creadas",
    ["endpoint"],
)

IDEMPOTENCY_KEYS_EXPIRED = Counter(
    "idempotency_keys_expired_total",
    "Claves de idempotencia expiradas y eliminadas",
    ["endpoint"],
)

IDEMPOTENCY_PROCESSING_TIME = Histogram(
    "idempotency_processing_time_seconds",
    "Tiempo de procesamiento del middleware de idempotencia",
    ["endpoint", "cache_result"],  # cache_result: hit, miss, error
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

IDEMPOTENCY_ERRORS = Counter(
    "idempotency_errors_total",
    "Errores en el middleware de idempotencia (fail-open)",
    ["endpoint", "error_type"],
)
