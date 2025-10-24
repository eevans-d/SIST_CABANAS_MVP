#!/usr/bin/env python3
"""Concurrency Overlap Test (Módulo 2).

Lanza dos pre-reservas concurrentes al mismo alojamiento y rango de fechas.
Objetivo: observar que no ambas sean exitosas (esperado: una deba fallar con error
`date_overlap` si Postgres + EXCLUDE gist está activo y/o el lock Redis previene carrera).

Por defecto NO ejecuta pruebas que mutan estado. Debe habilitarse con RUN_MUTATING=1.

Uso:
  BASE_URL=http://localhost:8000/api/v1 RUN_MUTATING=1 \
  python backend/scripts/concurrency_overlap_test.py

Notas:
- Este script no falla el proceso si ambas pasan (p.ej. SQLite sin EXCLUDE); imprime diagnóstico.
- Elegir fechas en el futuro para no interferir con reservaciones reales.
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, timedelta
from typing import Any, Dict, Optional

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
RUN_MUTATING = os.getenv("RUN_MUTATING", "0") == "1"


async def find_one_accommodation(client: httpx.AsyncClient) -> Optional[int]:
    """Devuelve el id de un alojamiento activo (el primero) o None si no hay."""
    r = await client.get(f"{BASE_URL}/reservations/accommodations", timeout=5)
    r.raise_for_status()
    data = r.json()
    if not data:
        return None
    return int(data[0]["id"])  # tomar el primero activo


async def post_prereserve(client: httpx.AsyncClient, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Realiza POST de pre-reserva y devuelve status + body parseado (o error)."""
    r = await client.post(f"{BASE_URL}/reservations/pre-reserve", json=payload, timeout=10)
    try:
        js = r.json()
    except Exception:
        js = {"error": f"invalid_json status={r.status_code}"}
    return {"status_code": r.status_code, "body": js}


async def main() -> None:
    """Ejecuta la prueba de concurrencia si RUN_MUTATING=1."""
    if not RUN_MUTATING:
        print("RUN_MUTATING!=1 → prueba desactivada. Establece RUN_MUTATING=1 para ejecutarla.")
        return

    async with httpx.AsyncClient() as client:
        acc_id = await find_one_accommodation(client)
        if not acc_id:
            print("No hay accommodations activos para probar.")
            return
        # Fechas futuras para minimizar interferencia
        ci = date.today() + timedelta(days=14)
        co = ci + timedelta(days=2)
        payload = {
            "accommodation_id": acc_id,
            "check_in": ci.isoformat(),
            "check_out": co.isoformat(),
            "guests": 2,
            "channel": "test",
            "contact_name": "Test Runner",
            "contact_phone": "+000000000",
            "contact_email": None,
        }
        t1, t2 = await asyncio.gather(
            post_prereserve(client, payload), post_prereserve(client, payload)
        )
        both_ok = (
            t1["status_code"] < 400
            and not t1["body"].get("error")
            and t2["status_code"] < 400
            and not t2["body"].get("error")
        )
        print(
            {
                "accommodation_id": acc_id,
                "check_in": ci.isoformat(),
                "check_out": co.isoformat(),
                "result1": t1,
                "result2": t2,
                "both_ok": both_ok,
                "note": (
                    "Si ambos OK, revisar Postgres EXCLUDE + btree_gist y locks Redis "
                    "en entorno actual."
                ),
            }
        )


if __name__ == "__main__":
    asyncio.run(main())
