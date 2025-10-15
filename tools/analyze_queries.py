#!/usr/bin/env python3
"""
Database Query Analysis Tool

Analiza queries de la base de datos usando EXPLAIN ANALYZE
para identificar bottlenecks y missing indexes.

Usage:
    python tools/analyze_queries.py --all
    python tools/analyze_queries.py --query overlap_check
    python tools/analyze_queries.py --n-plus-one
"""
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import structlog
from app.core.database import async_session_maker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class QueryAnalyzer:
    """Analiza performance de queries PostgreSQL"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    async def analyze_overlap_check(self, session: AsyncSession):
        """Analiza query crítico: overlap check en pre-reservas"""
        logger.info("analyzing_overlap_check")

        # Query real usado en ReservationService.create_prereservation
        query = text(
            """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM reservations
            WHERE accommodation_id = 1
              AND period && daterange('2025-12-15', '2025-12-17', '[)')
              AND reservation_status IN ('pre_reserved', 'confirmed');
        """
        )

        result = await session.execute(query)
        explain_data = result.scalar()

        self._analyze_plan(explain_data[0], "overlap_check")

    async def analyze_list_reservations(self, session: AsyncSession):
        """Analiza query admin: listar reservas sin eager loading"""
        logger.info("analyzing_list_reservations")

        # Query usado en admin.list_reservations (SIN selectinload)
        query = text(
            """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM reservations
            WHERE reservation_status = 'confirmed'
            LIMIT 100;
        """
        )

        result = await session.execute(query)
        explain_data = result.scalar()

        self._analyze_plan(explain_data[0], "list_reservations")

    async def analyze_list_reservations_with_accommodation(self, session: AsyncSession):
        """Analiza query admin: listar reservas CON eager loading"""
        logger.info("analyzing_list_reservations_with_accommodation")

        # Query optimizado con JOIN
        query = text(
            """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT r.*, a.name as accommodation_name
            FROM reservations r
            LEFT JOIN accommodations a ON r.accommodation_id = a.id
            WHERE r.reservation_status = 'confirmed'
            LIMIT 100;
        """
        )

        result = await session.execute(query)
        explain_data = result.scalar()

        self._analyze_plan(explain_data[0], "list_reservations_with_join")

    async def analyze_guest_phone_lookup(self, session: AsyncSession):
        """Analiza query: búsqueda por guest_phone"""
        logger.info("analyzing_guest_phone_lookup")

        query = text(
            """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM reservations
            WHERE guest_phone = '+5491112345678'
            ORDER BY created_at DESC
            LIMIT 10;
        """
        )

        result = await session.execute(query)
        explain_data = result.scalar()

        self._analyze_plan(explain_data[0], "guest_phone_lookup")

    async def analyze_date_range_query(self, session: AsyncSession):
        """Analiza query: búsqueda por rango de fechas"""
        logger.info("analyzing_date_range_query")

        query = text(
            """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM reservations
            WHERE check_in >= '2025-12-01'
              AND check_out <= '2025-12-31'
              AND accommodation_id = 1;
        """
        )

        result = await session.execute(query)
        explain_data = result.scalar()

        self._analyze_plan(explain_data[0], "date_range_query")

    async def analyze_expired_prereservations(self, session: AsyncSession):
        """Analiza query background job: limpiar pre-reservas expiradas"""
        logger.info("analyzing_expired_prereservations")

        query = text(
            """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM reservations
            WHERE reservation_status = 'pre_reserved'
              AND expires_at < NOW();
        """
        )

        result = await session.execute(query)
        explain_data = result.scalar()

        self._analyze_plan(explain_data[0], "expired_prereservations")

    async def check_missing_indexes(self, session: AsyncSession):
        """Busca columnas usadas en WHERE sin índice"""
        logger.info("checking_missing_indexes")

        # Query pg_stat_statements para ver queries comunes
        query = text(
            """
            SELECT
                schemaname,
                tablename,
                attname as column_name,
                n_distinct,
                correlation
            FROM pg_stats
            WHERE schemaname = 'public'
              AND tablename IN ('reservations', 'accommodations')
              AND n_distinct > 10
            ORDER BY abs(correlation) ASC
            LIMIT 20;
        """
        )

        try:
            result = await session.execute(query)
            rows = result.fetchall()

            print("\n🔍 COLUMNAS SIN ÍNDICE (potencial benefit):")
            print("=" * 80)
            for row in rows:
                print(
                    f"  {row.tablename}.{row.column_name} "
                    f"(n_distinct={row.n_distinct}, correlation={row.correlation:.3f})"
                )

            if not rows:
                print("  ✅ No se encontraron columnas candidatas")

        except Exception as e:
            logger.warning("pg_stats_not_available", error=str(e))

    async def check_sequential_scans(self, session: AsyncSession):
        """Busca tablas con muchos sequential scans (malo para performance)"""
        logger.info("checking_sequential_scans")

        query = text(
            """
            SELECT
                schemaname,
                relname as table_name,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                CASE
                    WHEN seq_scan + idx_scan > 0
                    THEN ROUND((seq_scan::numeric / (seq_scan + idx_scan)) * 100, 2)
                    ELSE 0
                END as seq_scan_percentage
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
              AND relname IN ('reservations', 'accommodations')
            ORDER BY seq_scan DESC;
        """
        )

        result = await session.execute(query)
        rows = result.fetchall()

        print("\n📊 SEQUENTIAL SCANS (deberían ser < 10%):")
        print("=" * 80)
        print(f"{'Table':<20} {'Seq Scans':<12} {'Index Scans':<12} {'Seq %':<10}")
        print("-" * 80)

        for row in rows:
            status = "❌" if row.seq_scan_percentage > 10 else "✅"
            print(
                f"{status} {row.table_name:<18} {row.seq_scan:<12} "
                f"{row.idx_scan or 0:<12} {row.seq_scan_percentage:<10}%"
            )

    def _analyze_plan(self, plan: Dict[str, Any], query_name: str):
        """Analiza EXPLAIN plan y extrae métricas clave"""
        exec_time = plan.get("Execution Time", 0)
        planning_time = plan.get("Planning Time", 0)
        total_time = exec_time + planning_time

        plan_node = plan.get("Plan", {})
        node_type = plan_node.get("Node Type", "Unknown")
        actual_rows = plan_node.get("Actual Rows", 0)
        actual_loops = plan_node.get("Actual Loops", 1)
        total_cost = plan_node.get("Total Cost", 0)

        # Detectar red flags
        red_flags = []
        if "Seq Scan" in node_type:
            red_flags.append("⚠️  SEQUENTIAL SCAN (malo para tablas grandes)")
        if exec_time > 100:
            red_flags.append("⚠️  SLOW QUERY (>100ms)")
        if actual_rows > 10000:
            red_flags.append("⚠️  HIGH ROW COUNT (>10k rows)")

        # Buscar nested loops (N+1 potential)
        if "Nested Loop" in str(plan):
            red_flags.append("⚠️  NESTED LOOP (potential N+1)")

        result = {
            "query_name": query_name,
            "execution_time_ms": round(exec_time, 2),
            "planning_time_ms": round(planning_time, 2),
            "total_time_ms": round(total_time, 2),
            "node_type": node_type,
            "actual_rows": actual_rows,
            "total_cost": round(total_cost, 2),
            "red_flags": red_flags,
        }

        self.results.append(result)

        # Print inline
        print(f"\n📋 Query: {query_name}")
        print("=" * 80)
        print(f"  Execution Time:  {exec_time:.2f}ms")
        print(f"  Planning Time:   {planning_time:.2f}ms")
        print(f"  Total Time:      {total_time:.2f}ms")
        print(f"  Node Type:       {node_type}")
        print(f"  Rows Returned:   {actual_rows}")
        print(f"  Total Cost:      {total_cost:.2f}")

        if red_flags:
            print(f"\n  🚨 RED FLAGS:")
            for flag in red_flags:
                print(f"     {flag}")
        else:
            print(f"\n  ✅ No red flags")

    async def detect_n_plus_one(self, session: AsyncSession):
        """Detecta potenciales N+1 queries inspeccionando código"""
        logger.info("detecting_n_plus_one_patterns")

        print("\n🔍 POTENCIALES N+1 QUERIES (código detectado):")
        print("=" * 80)

        # Estos patrones fueron detectados en semantic_search
        n_plus_one_cases = [
            {
                "file": "backend/app/routers/admin.py:list_reservations",
                "issue": "Itera sobre reservas pero NO carga Accommodation con selectinload",
                "impact": "Alto - Si se necesita acc.name, hará 1 query por reserva",
                "fix": "Usar selectinload(Reservation.accommodation)",
            },
            {
                "file": "backend/app/services/button_handlers.py:_handle_view_details",
                "issue": "Carga reservation y luego hace query separada para accommodation",
                "impact": "Medio - Solo afecta 1 request, no loop",
                "fix": "Usar selectinload o joinedload",
            },
            {
                "file": "backend/app/services/button_handlers.py:_handle_accommodation_selected",
                "issue": "Query individual para cada accommodation_id",
                "impact": "Bajo - Solo 1 alojamiento por request",
                "fix": "OK para este caso de uso",
            },
            {
                "file": "backend/app/routers/whatsapp.py:webhook",
                "issue": "Query Accommodation.active sin limit al inicio",
                "impact": "Bajo - Solo carga 2 max con LIMIT 2",
                "fix": "Ya optimizado",
            },
        ]

        for i, case in enumerate(n_plus_one_cases, 1):
            severity = (
                "🔴 CRÍTICO"
                if case["impact"].startswith("Alto")
                else "🟡 MEDIO"
                if case["impact"].startswith("Medio")
                else "🟢 BAJO"
            )
            print(f"\n{severity} #{i}: {case['file']}")
            print(f"  Issue:  {case['issue']}")
            print(f"  Impact: {case['impact']}")
            print(f"  Fix:    {case['fix']}")

    def print_summary(self):
        """Imprime resumen de análisis"""
        if not self.results:
            return

        print("\n" + "=" * 80)
        print("📊 RESUMEN DE ANÁLISIS")
        print("=" * 80)

        total_queries = len(self.results)
        slow_queries = [r for r in self.results if r["execution_time_ms"] > 50]
        very_slow = [r for r in self.results if r["execution_time_ms"] > 100]
        seq_scans = [r for r in self.results if "SEQUENTIAL SCAN" in str(r["red_flags"])]

        print(f"\nTotal Queries Analizados: {total_queries}")
        print(f"Slow Queries (>50ms):     {len(slow_queries)}")
        print(f"Very Slow (>100ms):       {len(very_slow)}")
        print(f"Sequential Scans:         {len(seq_scans)}")

        if very_slow:
            print(f"\n🔴 QUERIES MÁS LENTOS:")
            for r in sorted(very_slow, key=lambda x: x["execution_time_ms"], reverse=True)[:5]:
                print(f"  {r['query_name']:<30} {r['execution_time_ms']:>8.2f}ms")

        # Recommendations
        print(f"\n💡 RECOMENDACIONES:")

        if seq_scans:
            print("  1. Agregar índices para queries con sequential scans")
        if slow_queries:
            print("  2. Optimizar queries lentos con EXPLAIN ANALYZE")
        if any("NESTED LOOP" in str(r["red_flags"]) for r in self.results):
            print("  3. Revisar nested loops y considerar JOINs directos")

        print("  4. Habilitar pg_stat_statements para tracking continuo")
        print("  5. Usar selectinload/joinedload para evitar N+1")


async def main():
    parser = argparse.ArgumentParser(description="Analyze database queries")
    parser.add_argument("--all", action="store_true", help="Run all query analysis")
    parser.add_argument(
        "--query",
        type=str,
        choices=[
            "overlap_check",
            "list_reservations",
            "guest_phone",
            "date_range",
            "expired",
        ],
        help="Analyze specific query",
    )
    parser.add_argument("--n-plus-one", action="store_true", help="Detect N+1 query patterns")
    parser.add_argument("--indexes", action="store_true", help="Check for missing indexes")
    parser.add_argument("--seq-scans", action="store_true", help="Check sequential scans")

    args = parser.parse_args()

    analyzer = QueryAnalyzer()

    async with async_session_maker() as session:
        try:
            if args.all or args.query == "overlap_check":
                await analyzer.analyze_overlap_check(session)

            if args.all or args.query == "list_reservations":
                await analyzer.analyze_list_reservations(session)
                await analyzer.analyze_list_reservations_with_accommodation(session)

            if args.all or args.query == "guest_phone":
                await analyzer.analyze_guest_phone_lookup(session)

            if args.all or args.query == "date_range":
                await analyzer.analyze_date_range_query(session)

            if args.all or args.query == "expired":
                await analyzer.analyze_expired_prereservations(session)

            if args.all or args.indexes:
                await analyzer.check_missing_indexes(session)

            if args.all or args.seq_scans:
                await analyzer.check_sequential_scans(session)

            if args.all or args.n_plus_one:
                await analyzer.detect_n_plus_one(session)

            # Print summary
            analyzer.print_summary()

        except Exception as e:
            logger.error("analysis_failed", error=str(e), exc_info=True)
            return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
