from __future__ import annotations

from prometheus_client import Counter

# Contadores/Métricas centralizados para evitar registros duplicados en el registry

NLU_PRE_RESERVE = Counter(
    "nlu_pre_reserve_total",
    "Acciones NLU hacia pre-reserva",
    ["action", "source"],
)
