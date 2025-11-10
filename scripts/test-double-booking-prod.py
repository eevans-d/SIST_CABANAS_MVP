#!/usr/bin/env python3
"""
Prueba concurrente de doble-booking contra un entorno desplegado (Railway).

Contrato esperado:
- Listado alojamientos: GET /api/v1/reservations/accommodations -> [ { id, name, ... } ]
- Pre-reserva: POST /api/v1/reservations/pre-reserve (JSON):
        {
            "accommodation_id": int,
            "check_in": "YYYY-MM-DD",
            "check_out": "YYYY-MM-DD",
            "guests": 2,
            "channel": "script",
            "contact_name": "Tester",
            "contact_phone": "+000000000",
            "contact_email": null
        }

Éxito de la prueba:
- 1 solicitud devuelve un objeto con "code" (pre-reserva creada)
- El resto responde con {"error": "date_overlap"} o {"error": "processing_or_unavailable"}

Uso:
    BASE_URL=https://<tu-app>.up.railway.app \
        scripts/test-double-booking-prod.py \
        --concurrency 10 --offset-days 7 --nights 2

Exit codes:
- 0: exclusión verificada (<=1 éxito y >=1 errores de solapamiento)
- 1: condición no cumplida
"""

import argparse
import asyncio
import os
import sys
from datetime import date, timedelta
from typing import Any

import httpx


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI para la prueba de doble-booking.

    Retorna:
        argparse.Namespace con base_url, concurrency, offset_days y nights.
    """
    p = argparse.ArgumentParser(description="Concurrent double-booking test (prod)")
    p.add_argument(
        "--base-url",
        default=os.environ.get("BASE_URL", ""),
        help="API base URL, e.g. https://app.up.railway.app",
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Concurrent requests (default 10)",
    )
    p.add_argument(
        "--offset-days",
        type=int,
        default=7,
        help="Days from today until check_in (default 7)",
    )
    p.add_argument(
        "--nights",
        type=int,
        default=2,
        help="Number of nights for the reservation (default 2)",
    )
    return p.parse_args()


async def fetch_accommodation_id(client: httpx.AsyncClient, base_url: str) -> int:
    """Obtener un accommodation ID válido para la prueba (toma el primero activo)."""
    r = await client.get(f"{base_url}/api/v1/reservations/accommodations", timeout=20)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or not data:
        raise RuntimeError("No accommodations available to test")
    return int(data[0]["id"])  # Tomar el primero activo


async def create_prereserve(
    client: httpx.AsyncClient,
    base_url: str,
    payload: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """Intentar crear una pre-reserva; devuelve (exito_http, json)."""
    try:
        r = await client.post(
            f"{base_url}/api/v1/reservations/pre-reserve", json=payload, timeout=20
        )
        ok = r.status_code in (200, 201)
        data = r.json() if r.content else {"error": f"http_{r.status_code}"}
        return ok, data
    except Exception as e:
        return False, {"error": str(e)}


async def main() -> int:
    """Ejecuta la prueba concurrente de doble-booking y retorna exit code acorde al resultado."""
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    if not base_url.startswith("http"):
        print(
            "ERROR: BASE_URL no establecido (usa --base-url o variable BASE_URL)", file=sys.stderr
        )
        return 2

    check_in = date.today() + timedelta(days=args.offset_days)
    check_out = check_in + timedelta(days=args.nights)

    async with httpx.AsyncClient() as client:
        acc_id = await fetch_accommodation_id(client, base_url)

        payload = {
            "accommodation_id": acc_id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": 2,
            "channel": "loadtest",
            "contact_name": "Carga Concurrency",
            "contact_phone": "+540000000",
            "contact_email": None,
        }

        tasks = [create_prereserve(client, base_url, payload) for _ in range(args.concurrency)]
    results: list[tuple[bool, dict[str, Any]]] = await asyncio.gather(*tasks)

    successes = [d for ok, d in results if ok and isinstance(d, dict) and d.get("code")]
    errors = [d for ok, d in results if not (ok and d.get("code"))]

    # Métrica de verificación
    success_count = len(successes)
    overlap_errors = sum(
        1
        for d in errors
        if (
            isinstance(d, dict)
            and d.get("error")
            in (
                "date_overlap",
                "processing_or_unavailable",
            )
        )
    )

    print("\n=== Double-Booking Test Summary ===")
    print(f"Base URL: {base_url}")
    print(f"Accommodation ID: {acc_id}")
    print(f"Dates: {check_in} -> {check_out} ({args.nights} nights)")
    print(f"Concurrency: {args.concurrency}")
    print(f"Successes with code: {success_count}")
    print(f"Expected errors (overlap/lock): {overlap_errors}")
    print(f"Other results: {len(results) - success_count - overlap_errors}")

    # Éxito ideal: exactamente 1 éxito, resto errores esperados
    if success_count == 1 and overlap_errors >= (args.concurrency - 1):
        print("✅ Anti double-booking verificado: solo una pre-reserva creada")
        print("Resto rechazadas.")
        return 0

    # Aceptar también 0 éxitos si todos chocan con lock (poco probable
    # pero posible bajo alta contención)
    if success_count == 0 and overlap_errors >= 1:
        print("⚠️ Resultado aceptable: 0 éxitos (lock alto),")
        print("todas rechazadas por solapamiento/lock.")
        return 0

    print("❌ Resultado no esperado. Muestra de respuestas:")
    for ok, d in results[:5]:
        print(ok, d)
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
