#!/usr/bin/env python3
"""
Performance Profiling Script - Sistema MVP

Ejecuta profiling detallado de endpoints críticos:
- Pre-reserva (create_prereservation)
- Webhook processing (WhatsApp, Mercado Pago)
- Audio transcription (transcribe_audio)
- NLU analysis

Genera reportes detallados con cProfile + visualizaciones con snakeviz.

Uso:
    python tools/profile_performance.py --endpoint prereservation --requests 100
    python tools/profile_performance.py --endpoint webhook --requests 50
    python tools/profile_performance.py --all --duration 30
"""

import argparse
import asyncio
import cProfile
import json
import os
import pstats
import sys
import time
from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import async_session_maker
from app.models.accommodation import Accommodation
from app.services.nlu import NLUService
from app.services.reservations import ReservationService
from sqlalchemy import select


class PerformanceProfiler:
    """Profiler para endpoints críticos del sistema"""

    def __init__(self, output_dir: str = "profiling_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.nlu = NLUService()
        self.results: Dict[str, Any] = {}

    async def setup_test_data(self):
        """Crear datos de prueba para profiling"""
        async with async_session_maker() as session:
            # Verificar si ya existe accommodation de test
            result = await session.execute(
                select(Accommodation).where(Accommodation.name == "Test Profiling Cabin")
            )
            acc = result.scalar_one_or_none()

            if not acc:
                acc = Accommodation(
                    name="Test Profiling Cabin",
                    type="cabin",
                    capacity=4,
                    base_price=10000.0,
                    description="Test accommodation for profiling",
                    amenities={},
                    photos=[],
                    location={},
                    policies={},
                    active=True,
                )
                session.add(acc)
                await session.commit()
                await session.refresh(acc)

            return acc.id

    async def profile_prereservation(self, num_requests: int = 100) -> Dict[str, Any]:
        """Profile del flujo completo de pre-reserva"""
        print(f"\n🔍 Profiling Pre-Reserva ({num_requests} requests)...")

        accommodation_id = await self.setup_test_data()
        reservation_service = ReservationService()

        # Preparar datos de prueba
        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        profiler = cProfile.Profile()
        profiler.enable()

        # Ejecutar requests
        start_time = time.monotonic()
        successful = 0
        errors = 0

        for i in range(num_requests):
            try:
                # Variar fechas para evitar overlaps
                check_in_var = check_in + timedelta(days=i * 3)
                check_out_var = check_in_var + timedelta(days=2)

                result = await reservation_service.create_prereservation(
                    accommodation_id=accommodation_id,
                    check_in=check_in_var,
                    check_out=check_out_var,
                    guests=2,
                    channel="test",
                    contact_name="Test User",
                    contact_phone=f"+5491112345{i:03d}",
                    contact_email=f"test{i}@example.com",
                )

                if "error" not in result:
                    successful += 1
                else:
                    errors += 1

            except Exception as e:
                errors += 1
                print(f"  ⚠️  Error en request {i}: {e}")

        end_time = time.monotonic()
        profiler.disable()

        # Generar stats
        stats_output = StringIO()
        stats = pstats.Stats(profiler, stream=stats_output)
        stats.sort_stats("cumulative")
        stats.print_stats(30)  # Top 30 funciones

        # Guardar profiling data
        profile_file = (
            self.output_dir / f"prereservation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.prof"
        )
        stats.dump_stats(str(profile_file))

        # Calcular métricas
        total_time = end_time - start_time
        avg_time = total_time / num_requests if num_requests > 0 else 0

        result = {
            "endpoint": "create_prereservation",
            "num_requests": num_requests,
            "successful": successful,
            "errors": errors,
            "total_time_seconds": round(total_time, 2),
            "avg_time_ms": round(avg_time * 1000, 2),
            "requests_per_second": round(num_requests / total_time, 2),
            "profile_file": str(profile_file),
            "top_functions": stats_output.getvalue().split("\n")[:35],
        }

        print(f"  ✅ Completado: {successful}/{num_requests} exitosos")
        print(f"  ⏱️  Tiempo promedio: {result['avg_time_ms']} ms")
        print(f"  📊 Throughput: {result['requests_per_second']} req/s")
        print(f"  💾 Profile guardado: {profile_file}")

        return result

    async def profile_nlu(self, num_requests: int = 1000) -> Dict[str, Any]:
        """Profile del servicio NLU"""
        print(f"\n🔍 Profiling NLU Analysis ({num_requests} requests)...")

        # Mensajes de prueba variados
        test_messages = [
            "Hola, quiero reservar para el finde del 15",
            "Cuánto sale la cabaña grande?",
            "Hay disponibilidad para 4 personas?",
            "Quiero hacer una reserva para diciembre",
            "Tienen wifi?",
            "audio de 10 segundos sobre disponibilidad",
            "¿El precio incluye desayuno?",
            "Necesito cancelar mi reserva",
        ]

        profiler = cProfile.Profile()
        profiler.enable()

        start_time = time.monotonic()

        for i in range(num_requests):
            message = test_messages[i % len(test_messages)]
            result = self.nlu.analyze_message(message)

        end_time = time.monotonic()
        profiler.disable()

        # Generar stats
        stats_output = StringIO()
        stats = pstats.Stats(profiler, stream=stats_output)
        stats.sort_stats("cumulative")
        stats.print_stats(30)

        # Guardar profiling data
        profile_file = self.output_dir / f"nlu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.prof"
        stats.dump_stats(str(profile_file))

        # Calcular métricas
        total_time = end_time - start_time
        avg_time = total_time / num_requests if num_requests > 0 else 0

        result = {
            "endpoint": "nlu_analyze",
            "num_requests": num_requests,
            "total_time_seconds": round(total_time, 2),
            "avg_time_ms": round(avg_time * 1000, 2),
            "requests_per_second": round(num_requests / total_time, 2),
            "profile_file": str(profile_file),
            "top_functions": stats_output.getvalue().split("\n")[:35],
        }

        print(f"  ⏱️  Tiempo promedio: {result['avg_time_ms']} ms")
        print(f"  📊 Throughput: {result['requests_per_second']} req/s")
        print(f"  💾 Profile guardado: {profile_file}")

        return result

    async def profile_database_queries(self) -> Dict[str, Any]:
        """Profile de queries comunes de DB"""
        print(f"\n🔍 Profiling Database Queries...")

        from sqlalchemy import text

        queries = {
            "select_accommodations": "SELECT * FROM accommodations WHERE active = true",
            "check_availability": """
                SELECT * FROM reservations
                WHERE accommodation_id = 1
                  AND period && daterange('2025-12-01', '2025-12-03', '[)')
                  AND reservation_status IN ('pre_reserved', 'confirmed')
            """,
            "list_reservations": """
                SELECT r.*, a.name as accommodation_name
                FROM reservations r
                JOIN accommodations a ON r.accommodation_id = a.id
                WHERE r.reservation_status = 'confirmed'
                ORDER BY r.check_in DESC
                LIMIT 50
            """,
            "accommodation_with_reservations": """
                SELECT a.*, r.*
                FROM accommodations a
                LEFT JOIN reservations r ON a.id = r.accommodation_id
                WHERE a.active = true
            """,
        }

        results = {}

        async with async_session_maker() as session:
            for query_name, sql in queries.items():
                timings = []

                # Ejecutar 100 veces para obtener avg
                for _ in range(100):
                    start = time.monotonic()
                    await session.execute(text(sql))
                    duration = (time.monotonic() - start) * 1000  # ms
                    timings.append(duration)

                # Calcular métricas
                timings.sort()
                results[query_name] = {
                    "query": sql.strip()[:100] + "...",
                    "avg_ms": round(sum(timings) / len(timings), 2),
                    "p50_ms": round(timings[len(timings) // 2], 2),
                    "p95_ms": round(timings[int(len(timings) * 0.95)], 2),
                    "p99_ms": round(timings[int(len(timings) * 0.99)], 2),
                    "min_ms": round(min(timings), 2),
                    "max_ms": round(max(timings), 2),
                }

                print(f"  📊 {query_name}:")
                print(
                    f"     Avg: {results[query_name]['avg_ms']} ms | "
                    f"P95: {results[query_name]['p95_ms']} ms"
                )

        return {
            "endpoint": "database_queries",
            "queries": results,
        }

    def generate_report(self) -> str:
        """Generar reporte consolidado de profiling"""
        report_path = (
            self.output_dir / f"profiling_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        report = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "summary": {
                "total_endpoints_profiled": len(self.results),
                "profile_files": [
                    str(r.get("profile_file", ""))
                    for r in self.results.values()
                    if "profile_file" in r
                ],
            },
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Reporte guardado: {report_path}")
        print(f"\n📊 Para visualizar profiles, usa:")
        for profile_file in report["summary"]["profile_files"]:
            if profile_file:
                print(f"   snakeviz {profile_file}")

        return str(report_path)


async def main():
    parser = argparse.ArgumentParser(description="Performance Profiling Tool")
    parser.add_argument(
        "--endpoint",
        choices=["prereservation", "nlu", "database", "all"],
        default="all",
        help="Endpoint a profilear",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Número de requests para profiling",
    )
    parser.add_argument(
        "--output-dir",
        default="profiling_results",
        help="Directorio para guardar resultados",
    )

    args = parser.parse_args()

    profiler = PerformanceProfiler(output_dir=args.output_dir)

    print("=" * 70)
    print("🔬 PERFORMANCE PROFILING - Sistema MVP")
    print("=" * 70)

    if args.endpoint in ["prereservation", "all"]:
        result = await profiler.profile_prereservation(num_requests=args.requests)
        profiler.results["prereservation"] = result

    if args.endpoint in ["nlu", "all"]:
        result = await profiler.profile_nlu(num_requests=args.requests * 10)
        profiler.results["nlu"] = result

    if args.endpoint in ["database", "all"]:
        result = await profiler.profile_database_queries()
        profiler.results["database"] = result

    # Generar reporte consolidado
    report_path = profiler.generate_report()

    print("\n" + "=" * 70)
    print("✅ PROFILING COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
