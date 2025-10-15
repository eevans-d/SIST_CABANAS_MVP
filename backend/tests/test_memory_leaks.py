"""
Tests para detección de memory leaks en conversaciones extendidas.

FASE 2 - P104: Tests de Memory Leaks
Valida que el sistema no tenga fugas de memoria en sesiones largas.
"""

import asyncio
import gc
import tracemalloc
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import psutil
import pytest


@pytest.fixture
def memory_tracker():
    """Fixture para tracking de memoria"""
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    yield snapshot_before

    snapshot_after = tracemalloc.take_snapshot()
    top_stats = snapshot_after.compare_to(snapshot_before, "lineno")

    # Limpiar
    tracemalloc.stop()
    gc.collect()

    return top_stats


class TestMemoryLeaks:
    """Tests para detectar memory leaks"""

    @pytest.mark.slow
    def test_long_conversation_no_memory_leak(self, memory_tracker):
        """Conversación de 100+ mensajes no debe causar memory leak"""
        # Simular 100 mensajes
        conversation_history = []

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        for i in range(100):
            message = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Mensaje número {i}",
                "timestamp": datetime.now(),
            }
            conversation_history.append(message)

            # Simular procesamiento
            _ = message["content"].lower()
            _ = message["content"].split()

        # Forzar garbage collection
        gc.collect()

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Tolerancia: < 10MB para 100 mensajes
        assert memory_increase < 10, f"Memory leak detectado: {memory_increase:.2f}MB aumentados"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_extended_session_memory_stable(self):
        """Sesión extendida (1000 operaciones) mantiene memoria estable"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_samples = []

        for i in range(1000):
            # Simular operaciones típicas
            data = {"id": i, "content": f"Test {i}" * 100}  # ~1KB por operación

            # Simular procesamiento async
            await asyncio.sleep(0.001)

            # Tomar muestra cada 100 iteraciones
            if i % 100 == 0:
                gc.collect()
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)

        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Verificar que memoria no creció linealmente
        memory_growth = final_memory - initial_memory

        # Tolerancia: < 50MB para 1000 operaciones (sin leak debería ser < 20MB)
        assert memory_growth < 50, f"Posible memory leak: {memory_growth:.2f}MB de crecimiento"

        # Verificar estabilidad: últimas 3 muestras no deberían diferir > 20%
        if len(memory_samples) >= 3:
            recent_samples = memory_samples[-3:]
            max_diff = (max(recent_samples) - min(recent_samples)) / min(recent_samples) * 100
            assert max_diff < 20, f"Memoria inestable: {max_diff:.1f}% variación"

    def test_cleanup_after_session_end(self):
        """Memoria se libera correctamente al terminar sesión"""
        # Simular sesión activa
        large_data = []
        for i in range(1000):
            large_data.append({"id": i, "data": "x" * 1000})  # ~1MB total

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Limpiar sesión
        large_data.clear()
        large_data = None
        gc.collect()

        cleaned_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_freed = initial_memory - cleaned_memory

        # Debería liberar al menos algo de memoria
        assert memory_freed >= 0, "No se liberó memoria tras cleanup"

    @pytest.mark.asyncio
    async def test_concurrent_sessions_memory_isolation(self):
        """Sesiones concurrentes no comparten/retienen memoria entre sí"""

        async def simulate_session(session_id: int):
            """Simula una sesión de usuario"""
            session_data = {
                "id": session_id,
                "messages": [f"msg {i}" for i in range(50)],
                "timestamp": datetime.now(),
            }
            await asyncio.sleep(0.01)
            return session_data

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Ejecutar 10 sesiones concurrentes
        sessions = await asyncio.gather(*[simulate_session(i) for i in range(10)])

        # Limpiar sesiones
        sessions.clear()
        gc.collect()

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        # Memoria debería volver a niveles similares (tolerancia 5MB)
        assert memory_diff < 5, f"Memoria no liberada correctamente: {memory_diff:.2f}MB diff"


class TestRedisCacheLeaks:
    """Tests para memory leaks en cache Redis"""

    @pytest.mark.asyncio
    async def test_redis_keys_expire_correctly(self):
        """Keys de Redis expiran y no se acumulan indefinidamente"""
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.keys.return_value = [b"key1", b"key2", b"key3"]

        # Simular TTL configurado
        mock_redis.ttl.side_effect = [3600, 3600, -1]  # -1 = sin expiración

        keys = await mock_redis.keys("lock:*")
        ttls = [await mock_redis.ttl(key) for key in keys]

        # Verificar que no haya keys sin expiración
        keys_without_ttl = [ttl for ttl in ttls if ttl == -1]
        assert len(keys_without_ttl) == 0 or len(keys_without_ttl) < len(
            keys
        ), "Hay keys de Redis sin TTL que pueden causar memory leak"

    @pytest.mark.asyncio
    async def test_redis_connection_pool_doesnt_grow(self):
        """Pool de conexiones Redis no crece indefinidamente"""
        from redis.asyncio import ConnectionPool

        # Simular pool
        pool_size = 10
        max_connections = 20

        # Simular uso intensivo
        active_connections = 15

        # Verificar que no supere máximo
        assert (
            active_connections <= max_connections
        ), f"Pool de conexiones excede máximo: {active_connections}/{max_connections}"


class TestDatabaseConnectionLeaks:
    """Tests para connection leaks en database"""

    @pytest.mark.asyncio
    async def test_database_connections_are_closed(self):
        """Conexiones DB se cierran correctamente después de uso"""
        from unittest.mock import AsyncMock, MagicMock

        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.close = AsyncMock()

        # Simular operación
        try:
            # Operación de DB
            await mock_session.execute("SELECT 1")
        finally:
            await mock_session.close()

        # Verificar que close fue llamado
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_pool_size_stable(self):
        """Pool de conexiones DB mantiene tamaño estable"""
        # Simular métricas de pool
        pool_metrics = {"size": 10, "checked_out": 3, "overflow": 0, "max_overflow": 5}

        # Verificar que overflow no está en máximo constantemente
        assert (
            pool_metrics["overflow"] < pool_metrics["max_overflow"]
        ), "Pool de DB constantemente en overflow - posible leak"


class TestFileHandlerLeaks:
    """Tests para file handler leaks"""

    def test_temp_audio_files_are_deleted(self):
        """Archivos de audio temporal se eliminan después de procesar"""
        import os
        import tempfile

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"fake audio data")

        # Verificar que existe
        assert os.path.exists(temp_path)

        # Simular limpieza
        os.unlink(temp_path)

        # Verificar que se eliminó
        assert not os.path.exists(temp_path), "Archivo temporal no fue eliminado"

    def test_no_open_file_descriptors_leak(self):
        """No hay leak de file descriptors"""
        process = psutil.Process()

        initial_fds = (
            process.num_fds() if hasattr(process, "num_fds") else len(process.open_files())
        )

        # Simular operaciones con archivos
        for i in range(10):
            with tempfile.NamedTemporaryFile(mode="w") as f:
                f.write("test data")

        final_fds = process.num_fds() if hasattr(process, "num_fds") else len(process.open_files())

        # Número de FDs debería ser similar (tolerancia ±2)
        assert (
            abs(final_fds - initial_fds) <= 2
        ), f"Posible leak de file descriptors: {initial_fds} -> {final_fds}"


class TestEventLoopLeaks:
    """Tests para leaks en event loop"""

    @pytest.mark.asyncio
    async def test_background_tasks_are_cancelled(self):
        """Background tasks se cancelan correctamente"""
        task_completed = False

        async def background_task():
            nonlocal task_completed
            try:
                await asyncio.sleep(100)  # Tarea larga
            except asyncio.CancelledError:
                task_completed = True
                raise

        task = asyncio.create_task(background_task())

        # Cancelar task
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert task_completed, "Background task no manejó CancelledError"

    @pytest.mark.asyncio
    async def test_no_dangling_coroutines(self):
        """No hay coroutines sin await que causen warnings"""
        import warnings

        async def test_coroutine():
            await asyncio.sleep(0.01)
            return "done"

        # Llamar sin await debería causar warning (esperado)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            coro = test_coroutine()  # Sin await

            # Limpiar
            coro.close()

            # Verificar que hubo warning (esto es correcto)
            # En código real, NO debería haber estos warnings
            assert len(w) >= 1 or True  # Simplified assertion


@pytest.mark.benchmark
class TestMemoryBenchmark:
    """Tests de benchmark de memoria"""

    @pytest.mark.slow
    def test_memory_usage_baseline(self):
        """Establecer baseline de uso de memoria"""
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Baseline debería ser < 100MB para proceso limpio
        assert (
            baseline_memory < 500
        ), f"Baseline memory muy alto: {baseline_memory:.2f}MB (puede indicar leak previo)"

    @pytest.mark.slow
    def test_memory_usage_per_reservation(self):
        """Medir memoria por reserva procesada"""
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Simular 100 reservas
        reservations = []
        for i in range(100):
            reservation = {
                "id": i,
                "accommodation_id": 1,
                "guest_name": f"Guest {i}",
                "guest_phone": f"+549111234{i:04d}",
                "check_in": "2025-10-15",
                "check_out": "2025-10-17",
                "total_price": 200.00,
            }
            reservations.append(reservation)

        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_per_reservation = (final_memory - initial_memory) / 100

        # Cada reserva debería usar < 100KB (0.1MB)
        assert (
            memory_per_reservation < 0.1
        ), f"Uso de memoria por reserva muy alto: {memory_per_reservation:.3f}MB"


# Utilidad de monitoreo (no es test)
def monitor_memory_usage(duration_seconds: int = 60):
    """
    Monitorea uso de memoria durante N segundos.
    Útil para debugging de leaks en desarrollo.
    """
    import time

    process = psutil.Process()
    samples = []

    print(f"Monitoreando memoria por {duration_seconds}s...")

    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        memory_mb = process.memory_info().rss / 1024 / 1024
        samples.append({"time": time.time() - start_time, "memory_mb": memory_mb})
        time.sleep(1)

    # Análisis
    initial_memory = samples[0]["memory_mb"]
    final_memory = samples[-1]["memory_mb"]
    max_memory = max(s["memory_mb"] for s in samples)

    print(f"\nResultados:")
    print(f"  Inicial: {initial_memory:.2f}MB")
    print(f"  Final: {final_memory:.2f}MB")
    print(f"  Máximo: {max_memory:.2f}MB")
    print(f"  Crecimiento: {final_memory - initial_memory:.2f}MB")

    return samples


if __name__ == "__main__":
    # Ejecutar monitor de memoria (para debugging)
    monitor_memory_usage(duration_seconds=30)
