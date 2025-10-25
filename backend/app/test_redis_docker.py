import asyncio

import redis.asyncio as redis


async def test_redis_connection():
    """Test Redis connection with the configured URL"""
    # URL con la contraseña explícita
    redis_url = "redis://:redispass@redis:6379/0"

    try:
        # Crear conexión
        r = redis.from_url(redis_url, decode_responses=True)

        # Probar ping
        result = await r.ping()
        print(f"Redis PING: {result}")

        # Probar operaciones básicas
        await r.set("test_key", "test_value")
        value = await r.get("test_key")
        print(f"Redis GET: {value}")

        # Probar script Lua usando register_script
        script = r.register_script("return redis.call('GET', KEYS[1])")
        result = await script(keys=["test_key"])
        print(f"Redis EVAL con script registrado: {result}")

        await r.close()
        print("Test completo: Conexión exitosa a Redis")
    except Exception as e:
        print(f"Error al conectar a Redis: {e}")


if __name__ == "__main__":
    asyncio.run(test_redis_connection())
