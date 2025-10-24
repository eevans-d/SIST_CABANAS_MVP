#!/usr/bin/env python3
"""
Runtime Benchmark (Módulo 2).

Mide latencias de endpoints clave con concurrencia configurable y reporta p50/p95,
error rate y throughput simple. Por defecto NO realiza operaciones que muten estado.

Uso:
  BASE_URL=http://localhost:8000/api/v1 \
  CONCURRENCY=5 REQUESTS_PER_ENDPOINT=20 \
  python backend/scripts/runtime_benchmark.py

Variables:
- BASE_URL: URL base del API (con prefijo), ej: http://localhost:8000/api/v1
- CONCURRENCY: conexiones simultáneas por endpoint (default 5)
- REQUESTS_PER_ENDPOINT: cantidad de requests por endpoint (default 20)
- TIMEOUT: timeout por request en segundos (default 5)
- RUN_MUTATING: si "1", incluye pruebas que alteran estado (desactivado por defecto)
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import time
from typing import Any, Dict, List, Tuple

import httpx


def get_env_int(name: str, default: int) -> int:
    """Obtener entero de entorno con fallback seguro."""
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def get_root_from_base(base_url: str) -> str:
    """Derivar URL raíz a partir de BASE_URL, removiendo /api/v1 si corresponde."""
    if base_url.endswith("/api/v1"):
        return base_url[: -len("/api/v1")]
    return base_url


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
ROOT_URL = get_root_from_base(BASE_URL)
CONCURRENCY = get_env_int("CONCURRENCY", 5)
REQUESTS_PER_ENDPOINT = get_env_int("REQUESTS_PER_ENDPOINT", 20)
TIMEOUT = float(os.getenv("TIMEOUT", "5"))
RUN_MUTATING = os.getenv("RUN_MUTATING", "0") == "1"

# Endpoints read-only
READ_ONLY_ENDPOINTS: List[Tuple[str, str]] = [
    ("GET", f"{BASE_URL}/healthz"),
    ("GET", f"{BASE_URL}/readyz"),
    ("GET", f"{BASE_URL}/reservations/accommodations"),
]
# /metrics suele estar en raíz de la app, no bajo /api/v1
READ_ONLY_ENDPOINTS.append(("GET", f"{ROOT_URL}/metrics"))

# Endpoints mutantes (OPT-IN)
MUTATING_ENDPOINTS: List[Tuple[str, str, Dict[str, Any]]] = []
# Nota: /nlu/analyze podría crear pre-reservas si slots completos;
# se mantiene desactivado por defecto. Ejemplo si se usa:
# ("POST", f"{BASE_URL}/nlu/analyze", {"text": "quiero reservar"})


class Stats:
    """Acumulador de estadísticas de latencia y errores."""

    def __init__(self) -> None:
        """Inicializa estructuras internas."""
        self.latencies: List[float] = []
        self.errors: int = 0
        self.count: int = 0

    def add(self, latency: float, ok: bool) -> None:
        """Añadir una observación de latencia y si fue exitosa."""
        self.count += 1
        if ok:
            self.latencies.append(latency)
        else:
            self.errors += 1

    def summary(self) -> Dict[str, Any]:
        """Construir resumen con avg/p50/p95 y tasa de error."""
        if self.latencies:
            p50 = statistics.median(self.latencies)
            p95 = statistics.quantiles(self.latencies, n=100)[94]
            avg = statistics.fmean(self.latencies)
        else:
            p50 = p95 = avg = None
        return {
            "requests": self.count,
            "errors": self.errors,
            "error_rate": round(self.errors / self.count, 4) if self.count else None,
            "avg_ms": round((avg or 0) * 1000, 2) if avg is not None else None,
            "p50_ms": round(p50 * 1000, 2) if p50 is not None else None,
            "p95_ms": round(p95 * 1000, 2) if p95 is not None else None,
        }


async def worker(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    body: Dict[str, Any] | None,
    stats: Stats,
    total: int,
) -> None:
    """Ejecuta lote de peticiones y registra latencias/errores."""
    for _ in range(total):
        t0 = time.perf_counter()
        try:
            if method == "GET":
                r = await client.get(url)
            else:
                r = await client.post(url, json=body or {})
            ok = r.status_code < 500
        except Exception:
            ok = False
        dt = time.perf_counter() - t0
        stats.add(dt, ok)


async def run_endpoint(
    name: str, method: str, url: str, body: Dict[str, Any] | None
) -> Dict[str, Any]:
    """Ejecuta benchmark para un endpoint y devuelve resumen de métricas."""
    limits = httpx.Limits(max_connections=CONCURRENCY, max_keepalive_connections=CONCURRENCY)
    timeout = httpx.Timeout(TIMEOUT)
    stats = Stats()
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        per_worker = REQUESTS_PER_ENDPOINT // CONCURRENCY
        tasks = [
            asyncio.create_task(worker(client, method, url, body, stats, per_worker))
            for _ in range(CONCURRENCY)
        ]
        # Balancear si REQUESTS_PER_ENDPOINT no divide exacto
        remainder = REQUESTS_PER_ENDPOINT - per_worker * CONCURRENCY
        if remainder:
            tasks.append(asyncio.create_task(worker(client, method, url, body, stats, remainder)))
        await asyncio.gather(*tasks)
    return {"endpoint": url, "method": method, **stats.summary()}


async def main() -> None:
    """Punto de entrada: ejecuta benchmarks y emite resumen JSON."""
    print(
        json.dumps(
            {
                "base_url": BASE_URL,
                "root_url": ROOT_URL,
                "concurrency": CONCURRENCY,
                "requests_per_endpoint": REQUESTS_PER_ENDPOINT,
                "mutating": RUN_MUTATING,
            }
        )
    )
    results: List[Dict[str, Any]] = []

    # Read-only endpoints
    for method, url in READ_ONLY_ENDPOINTS:
        res = await run_endpoint(url, method, url, None)
        results.append(res)

    # Mutating endpoints (opt-in)
    if RUN_MUTATING:
        for method, url, body in MUTATING_ENDPOINTS:
            res = await run_endpoint(url, method, url, body)
            results.append(res)

    print(json.dumps({"results": results}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
