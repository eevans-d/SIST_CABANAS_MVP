#!/usr/bin/env python
"""
Prueba de las funciones de Redis lock (acquire, release, extend)
"""
import asyncio
import sys
import os

sys.path.insert(0, '/app')

from app.core.redis import get_redis, acquire_lock, release_lock, extend_lock

async def test_redis_locks():
    """Prueba las funciones de lock distribuido en Redis"""
    print("Probando funciones de lock distribuido en Redis...")
    
    # Obtener cliente Redis usando nuestro generador
    async for redis_client in get_redis():
        try:
            # Prueba 1: Adquirir un lock
            print("\n1. Probando acquire_lock...")
            lock_key = "test:lock:accommodation:123:2024-10-07:2024-10-10"
            lock_value = "reservation_instance_abc123"
            ttl = 1800  # 30 minutos
            
            lock_acquired = await acquire_lock(redis_client, lock_key, lock_value, ttl)
            print(f"   Lock adquirido: {lock_acquired}")
            
            # Verificar que el lock existe
            value = await redis_client.get(lock_key)
            print(f"   Valor del lock en Redis: {value}")
            
            # Prueba 2: Intentar adquirir el mismo lock (debería fallar)
            print("\n2. Probando acquire_lock duplicado (debería fallar)...")
            duplicate_lock = await acquire_lock(redis_client, lock_key, "otro_valor", ttl)
            print(f"   Lock duplicado: {duplicate_lock} (debería ser False)")
            
            # Prueba 3: Extender el lock
            print("\n3. Probando extend_lock...")
            lock_extended = await extend_lock(redis_client, lock_key, lock_value, 3600)
            print(f"   Lock extendido: {lock_extended}")
            
            # Verificar TTL
            ttl_remaining = await redis_client.ttl(lock_key)
            print(f"   TTL restante: {ttl_remaining} segundos")
            
            # Prueba 4: Intentar extender con valor incorrecto (debería fallar)
            print("\n4. Probando extend_lock con valor incorrecto...")
            wrong_extend = await extend_lock(redis_client, lock_key, "valor_incorrecto", 3600)
            print(f"   Extensión con valor incorrecto: {wrong_extend} (debería ser False)")
            
            # Prueba 5: Liberar el lock
            print("\n5. Probando release_lock...")
            lock_released = await release_lock(redis_client, lock_key, lock_value)
            print(f"   Lock liberado: {lock_released}")
            
            # Verificar que el lock ya no existe
            value_after_release = await redis_client.get(lock_key)
            print(f"   Valor después de liberar: {value_after_release} (debería ser None)")
            
            # Prueba 6: Intentar liberar el lock que ya no existe
            print("\n6. Probando release_lock en lock inexistente...")
            release_nonexistent = await release_lock(redis_client, lock_key, lock_value)
            print(f"   Liberar lock inexistente: {release_nonexistent} (debería ser False)")
            
            print("\n✅ Todas las pruebas de lock distribuido completadas exitosamente")
            
        except Exception as e:
            print(f"\n❌ Error en las pruebas de lock: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Limpiar: asegurar que el lock se libere
            try:
                await redis_client.delete(lock_key)
            except:
                pass
        
        break  # Salir del generador

if __name__ == "__main__":
    asyncio.run(test_redis_locks())