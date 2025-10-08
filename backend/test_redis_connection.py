#!/usr/bin/env python
"""
Script para probar la conexión a Redis con la nueva configuración.
"""
import asyncio
import sys
import os

# Asegurarse de que el directorio raíz esté en el path para las importaciones
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.config import get_settings
from app.core.redis import get_redis_pool, check_redis_health


async def test_redis_connection():
    """Prueba la conexión a Redis y muestra información de estado"""
    settings = get_settings()
    print(f"Configuración Redis:")
    redis_url = settings.REDIS_URL or "No configurado"
    if settings.REDIS_URL and "redispass" in settings.REDIS_URL:
        redis_url = settings.REDIS_URL.replace(":redispass@", ":***@")
    print(f"REDIS_URL: {redis_url}")
    print(f"REDIS_PASSWORD configurado: {'Sí' if settings.REDIS_PASSWORD else 'No'}")

    try:
        print("\nProbando obtener pool de conexión Redis...")
        pool = get_redis_pool()
        print("✅ Pool de conexión Redis obtenido correctamente")

        print("\nProbando verificar salud de Redis...")
        health = await check_redis_health()
        print(f"✅ Redis health check: {health}")

        # Verificamos si realmente podemos usar Redis para operaciones básicas
        print("\nProbando operaciones básicas en Redis...")
        import redis.asyncio as redis

        client = redis.Redis(connection_pool=pool)
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        print(f"✅ Operación básica SET/GET exitosa: {value.decode() if value else None}")

        # Probamos el uso de los scripts Lua
        print("\nProbando scripts Lua...")
        from app.core.redis import acquire_lock, release_lock

        lock_key = "test:lock"
        lock_value = "test_instance"
        lock_acquired = await acquire_lock(client, lock_key, lock_value)
        print(f"✅ Lock adquirido: {lock_acquired}")

        lock_released = await release_lock(client, lock_key, lock_value)
        print(f"✅ Lock liberado: {lock_released}")

        await client.close()
        print("\n✅ Todas las pruebas de conexión a Redis completadas con éxito")
    except Exception as e:
        print(f"\n❌ Error al conectar con Redis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_redis_connection())
