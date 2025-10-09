# 🎯 Roadmap MVP - Solo Prioridad Alta

## Filosofía: SHIPPING > PERFECCIÓN
Este roadmap incluye **ÚNICAMENTE** las características de **PRIORIDAD ALTA** que son necesarias y útiles para un MVP funcional, siguiendo la filosofía del proyecto: implementar solo lo necesario, sin feature creep.

---

## 📊 Resumen Ejecutivo

### Características Seleccionadas: 15 (de 106 analizadas)
- ✅ **Ya Implementadas:** 11
- 🔥 **Prioridad Alta para MVP:** 15 adicionales
- ⏱️ **Tiempo Estimado Total:** 3-4 semanas
- 🎯 **Objetivo:** MVP robusto, observable y listo para producción

### Criterios de Prioridad Alta
1. **Necesario para estabilidad:** Evita caídas, errores críticos
2. **Mejora UX básica:** Respuestas más claras sin complejidad
3. **Observabilidad:** Métricas y monitoreo esenciales
4. **Seguridad:** Protección contra abusos básicos

---

## 🚀 FASE 4: Optimización y Robustez (1.5-2 semanas)

### Objetivo
Llevar el MVP actual de "funciona" a "listo para producción" con observabilidad, robustez y mantenibilidad.

---

### 4.1 Background Jobs y Automatización (3-4 días)

#### 🔥 Prioridad Alta - Jobs que YA están en código pero sin monitoreo

**Características a Implementar:**

1. **Worker de Expiración de Pre-reservas**
   - **Estado Actual:** Implementado en `app/main.py` pero sin logs estructurados
   - **Mejora:** Agregar métricas y logging

   ```python
   # app/jobs/expire_prereservations.py
   from prometheus_client import Counter, Histogram

   PRERESERVATIONS_EXPIRED = Counter(
       'prereservations_expired_total',
       'Total de pre-reservas expiradas',
       ['accommodation_id']
   )

   PRERESERVATION_EXPIRY_DURATION = Histogram(
       'prereservation_expiry_job_duration_seconds',
       'Duración del job de expiración'
   )

   async def expire_prereservations_job():
       """Job que expira pre-reservas vencidas."""
       with PRERESERVATION_EXPIRY_DURATION.time():
           async with async_session_maker() as session:
               now = datetime.utcnow()
               stmt = select(Reservation).where(
                   Reservation.reservation_status == 'pre_reserved',
                   Reservation.expires_at < now
               )
               result = await session.execute(stmt)
               expired = result.scalars().all()

               for reservation in expired:
                   reservation.reservation_status = 'expired'
                   PRERESERVATIONS_EXPIRED.labels(
                       accommodation_id=reservation.accommodation_id
                   ).inc()
                   logger.info(
                       "prereservation_expired",
                       reservation_id=reservation.id,
                       code=reservation.code,
                       accommodation_id=reservation.accommodation_id
                   )

               await session.commit()
               return len(expired)
   ```

2. **Worker de Sincronización iCal**
   - **Estado Actual:** Código existe en `services/ical.py` pero sin scheduling
   - **Mejora:** Job periódico con control de errores

   ```python
   # app/jobs/sync_ical.py
   from prometheus_client import Gauge, Counter

   ICAL_SYNC_AGE_MINUTES = Gauge(
       'ical_last_sync_age_minutes',
       'Minutos desde última sync iCal',
       ['accommodation_id']
   )

   ICAL_SYNC_ERRORS = Counter(
       'ical_sync_errors_total',
       'Errores de sincronización iCal',
       ['accommodation_id', 'error_type']
   )

   async def sync_all_ical_feeds():
       """Sincronizar todos los feeds iCal configurados."""
       async with async_session_maker() as session:
           stmt = select(Accommodation).where(
               Accommodation.active == True,
               Accommodation.ical_feeds.isnot(None)
           )
           result = await session.execute(stmt)
           accommodations = result.scalars().all()

           for acc in accommodations:
               try:
                   await sync_ical_for_accommodation(acc.id)
                   ICAL_SYNC_AGE_MINUTES.labels(
                       accommodation_id=acc.id
                   ).set(0)
               except Exception as e:
                   ICAL_SYNC_ERRORS.labels(
                       accommodation_id=acc.id,
                       error_type=type(e).__name__
                   ).inc()
                   logger.error(
                       "ical_sync_failed",
                       accommodation_id=acc.id,
                       error=str(e)
                   )
   ```

**Tests:**
```bash
# backend/tests/test_background_jobs.py
async def test_expire_prereservations_job():
    """Debe expirar pre-reservas vencidas."""
    # Crear pre-reserva expirada
    # Ejecutar job
    # Verificar estado = 'expired'
    # Verificar métrica incrementada

async def test_ical_sync_job_handles_errors():
    """Debe manejar errores de feeds iCal inaccesibles."""
    # Mock feed con error 404
    # Ejecutar job
    # Verificar ICAL_SYNC_ERRORS incrementado
    # Verificar que otros feeds se procesan OK
```

**Estimación:** 3-4 días
**Valor:** Esencial para producción (pre-reservas se liberan automáticamente)

---

### 4.2 Health Checks Completos (2 días)

#### 🔥 Prioridad Alta - Monitoreo de servicios críticos

**Características a Implementar:**

3. **Health Check con Redis y DB**
   - **Estado Actual:** Endpoint básico existe
   - **Mejora:** Chequeos de latencia y estado de dependencias

   ```python
   # app/routers/health.py (ya existe, mejorar)
   @router.get("/healthz", response_model=HealthResponse)
   async def health_check():
       """Health check completo con latencias."""
       health_status = "healthy"
       checks = {}

       # Database check con latencia
       db_status = "ok"
       db_latency = 0
       try:
           start = time.monotonic()
           async with async_session_maker() as session:
               await session.execute(text("SELECT 1"))
           db_latency = round((time.monotonic() - start) * 1000)

           if db_latency > 500:
               health_status = "degraded"
               db_status = "slow"
       except Exception as e:
           db_status = "error"
           health_status = "unhealthy"
           logger.error("health_db_error", error=str(e))

       checks["database"] = {"status": db_status, "latency_ms": db_latency}

       # Redis check con latencia
       redis_status = "ok"
       redis_latency = 0
       try:
           start = time.monotonic()
           pool = await get_redis_pool()
           await pool.client().ping()
           redis_latency = round((time.monotonic() - start) * 1000)

           if redis_latency > 200:
               health_status = "degraded"
               redis_status = "slow"
       except Exception as e:
           redis_status = "error"
           health_status = "unhealthy"
           logger.error("health_redis_error", error=str(e))

       checks["redis"] = {"status": redis_status, "latency_ms": redis_latency}

       # iCal sync age check
       ical_status = "ok"
       try:
           max_age = await get_max_ical_sync_age_minutes()
           if max_age > 30:
               ical_status = "stale"
               if max_age > 60:
                   health_status = "degraded"
       except Exception as e:
           ical_status = "error"
           logger.error("health_ical_error", error=str(e))

       checks["ical_sync"] = {"status": ical_status, "max_age_minutes": max_age}

       return {
           "status": health_status,
           "timestamp": datetime.utcnow().isoformat(),
           "checks": checks
       }
   ```

4. **Readiness Check Separado**
   - Endpoint `/readyz` para Kubernetes/Docker health checks
   - Solo verifica que la app puede recibir requests

   ```python
   @router.get("/readyz")
   async def readiness_check():
       """Readiness check rápido."""
       return {"status": "ready"}
   ```

**Tests:**
```bash
# backend/tests/test_health.py
async def test_health_check_all_ok():
    """Health check debe retornar healthy cuando todo OK."""
    response = await client.get("/api/v1/healthz")
    assert response.json()["status"] == "healthy"
    assert response.json()["checks"]["database"]["status"] == "ok"

async def test_health_check_db_down():
    """Health check debe retornar unhealthy si DB falla."""
    # Mock DB connection error
    response = await client.get("/api/v1/healthz")
    assert response.json()["status"] == "unhealthy"
    assert response.json()["checks"]["database"]["status"] == "error"
```

**Estimación:** 2 días
**Valor:** Crítico para monitoreo y orquestación (Docker, K8s)

---

### 4.3 Rate Limiting y Protección Básica (2-3 días)

#### 🔥 Prioridad Alta - Evitar abusos y caídas

**Características a Implementar:**

5. **Rate Limit por IP en Webhooks**
   - Proteger endpoints públicos de spam
   - Usar Redis para contadores

   ```python
   # app/core/rate_limit.py
   from fastapi import Request, HTTPException
   from functools import wraps

   class RateLimiter:
       def __init__(self, redis_pool, max_requests: int, window_seconds: int):
           self.redis = redis_pool
           self.max_requests = max_requests
           self.window = window_seconds

       async def check_rate_limit(self, key: str) -> bool:
           """Verifica si se excedió el rate limit."""
           redis_conn = self.redis.client()
           current = await redis_conn.incr(key)

           if current == 1:
               await redis_conn.expire(key, self.window)

           return current <= self.max_requests

   # Middleware
   async def rate_limit_middleware(request: Request, call_next):
       """Middleware de rate limiting por IP."""

       # Bypass para health checks
       if request.url.path in ["/api/v1/healthz", "/api/v1/readyz", "/metrics"]:
           return await call_next(request)

       # Obtener IP (considerar X-Forwarded-For si detrás de proxy)
       client_ip = request.client.host
       if "X-Forwarded-For" in request.headers:
           client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()

       # Verificar rate limit
       rate_key = f"rate_limit:{client_ip}:{request.url.path}"
       limiter = RateLimiter(
           await get_redis_pool(),
           max_requests=100,  # 100 requests
           window_seconds=60  # por minuto
       )

       if not await limiter.check_rate_limit(rate_key):
           logger.warning(
               "rate_limit_exceeded",
               ip=client_ip,
               path=request.url.path
           )
           return JSONResponse(
               status_code=429,
               content={"error": "Too many requests"}
           )

       return await call_next(request)
   ```

6. **Validación de Tamaño de Payload**
   - Limitar tamaño de audio a 16MB (límite WhatsApp)
   - Rechazar requests muy grandes

   ```python
   # app/main.py
   app.add_middleware(
       RequestSizeLimitMiddleware,
       max_body_size=16 * 1024 * 1024  # 16MB
   )
   ```

**Tests:**
```bash
# backend/tests/test_rate_limit.py
async def test_rate_limit_blocks_after_limit():
    """Debe bloquear después de exceder límite."""
    # Hacer 100 requests rápidas
    for i in range(100):
        response = await client.post("/api/v1/webhooks/whatsapp", ...)
        assert response.status_code == 200

    # Request 101 debe fallar
    response = await client.post("/api/v1/webhooks/whatsapp", ...)
    assert response.status_code == 429
```

**Estimación:** 2-3 días
**Valor:** Protección esencial contra DDoS y abuso

---

### 4.4 Logging Estructurado Completo (1-2 días)

#### 🔥 Prioridad Alta - Debugging y troubleshooting

**Características a Implementar:**

7. **Trace ID en Todos los Requests**
   - Correlacionar logs de un mismo request
   - Útil para debugging de flujos complejos

   ```python
   # app/core/middleware.py
   import uuid
   from contextvars import ContextVar

   trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

   async def trace_id_middleware(request: Request, call_next):
       """Agrega trace ID a cada request."""
       trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
       trace_id_var.set(trace_id)

       response = await call_next(request)
       response.headers["X-Trace-ID"] = trace_id
       return response

   # En structlog config
   def add_trace_id(logger, method_name, event_dict):
       """Agrega trace_id a todos los logs."""
       trace_id = trace_id_var.get("")
       if trace_id:
           event_dict["trace_id"] = trace_id
       return event_dict

   structlog.configure(
       processors=[
           add_trace_id,
           structlog.processors.TimeStamper(fmt="iso"),
           structlog.processors.JSONRenderer()
       ]
   )
   ```

8. **Logs de Entrada/Salida de Servicios Críticos**
   - Log al inicio y fin de operaciones importantes
   - Incluir duración y resultado

   ```python
   # Decorador para servicios
   def log_service_call(operation: str):
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               start = time.monotonic()
               logger.info(f"{operation}_started", **kwargs)

               try:
                   result = await func(*args, **kwargs)
                   duration = time.monotonic() - start
                   logger.info(
                       f"{operation}_completed",
                       duration_ms=round(duration * 1000),
                       success=True
                   )
                   return result
               except Exception as e:
                   duration = time.monotonic() - start
                   logger.error(
                       f"{operation}_failed",
                       duration_ms=round(duration * 1000),
                       error=str(e),
                       error_type=type(e).__name__
                   )
                   raise
           return wrapper
       return decorator

   # Uso
   @log_service_call("create_prereservation")
   async def create_prereservation(self, ...):
       ...
   ```

**Tests:**
```bash
# Verificar en logs durante tests que trace_id existe
async def test_trace_id_in_logs(caplog):
    """Logs deben incluir trace_id."""
    response = await client.get("/api/v1/accommodations")

    # Verificar que logs tienen trace_id
    assert any("trace_id" in record.message for record in caplog.records)
```

**Estimación:** 1-2 días
**Valor:** Esencial para debugging en producción

---

## 🎯 FASE 5: Quick Wins UX (1-1.5 semanas)

### Objetivo
Mejoras rápidas de UX que no requieren complejidad técnica pero mejoran significativamente la experiencia.

---

### 5.1 Mensajes de Confirmación Claros (2-3 días)

#### 🔥 Prioridad Alta - Reducir confusión del usuario

**Características a Implementar:**

9. **Confirmación de Pre-reserva con Detalles**
   - Incluir resumen completo al confirmar pre-reserva
   - Link de pago directo

   ```python
   # app/services/whatsapp.py
   async def send_prereservation_confirmation(
       phone: str,
       reservation: Dict[str, Any],
       accommodation: Dict[str, Any],
       payment_link: str
   ):
       """Envía confirmación detallada de pre-reserva."""

       message = f"""✅ *Pre-reserva Confirmada*

   📋 *Código:* {reservation['code']}
   🏠 *Alojamiento:* {accommodation['name']}
   📅 *Check-in:* {reservation['check_in'].strftime('%d/%m/%Y')}
   📅 *Check-out:* {reservation['check_out'].strftime('%d/%m/%Y')}
   👥 *Huéspedes:* {reservation['guests_count']}
   💰 *Total:* ${reservation['total_price']:.2f}

   ⏰ *Importante:* Esta pre-reserva expira en 60 minutos.

   Para confirmar tu reserva, realiza el pago de la seña (${reservation['deposit_amount']:.2f}) aquí:
   {payment_link}

   ¿Necesitas ayuda? Responde a este mensaje."""

       await send_whatsapp_message(phone, message)
   ```

10. **Mensaje de Error Amigable con Sugerencias**
    - Cuando hay error, sugerir alternativas
    - Evitar mensajes técnicos

    ```python
    # app/services/nlu.py
    def format_error_message(error_type: str, context: Dict) -> str:
        """Formatea mensaje de error amigable."""

        if error_type == "date_overlap":
            return f"""Lo siento, las fechas {context['check_in']} a {context['check_out']} no están disponibles para {context['accommodation_name']}.

    ¿Te gustaría ver otras fechas disponibles? Puedo ayudarte a buscar."""

        elif error_type == "no_availability":
            return """No encontré disponibilidad para esas fechas en ninguno de nuestros alojamientos.

    ¿Quieres que te sugiera fechas cercanas con disponibilidad?"""

        elif error_type == "invalid_dates":
            return """Las fechas que indicaste no son válidas (quizás el check-out es antes del check-in, o las fechas ya pasaron).

    Por favor, intenta nuevamente. Ejemplo: "Del 15 al 20 de diciembre" """

        else:
            return """Ups, hubo un problema procesando tu solicitud.

    ¿Podrías reformular tu mensaje? Si el problema persiste, contacta a soporte."""
    ```

**Tests:**
```bash
# backend/tests/test_whatsapp_messages.py
async def test_prereservation_confirmation_has_all_details():
    """Confirmación debe incluir todos los detalles."""
    # Crear pre-reserva
    # Verificar mensaje WhatsApp enviado
    # Verificar que incluye: código, fechas, precio, link pago, tiempo expiración

async def test_error_message_is_user_friendly():
    """Mensajes de error no deben ser técnicos."""
    response = await create_prereservation_with_overlap()
    message = extract_whatsapp_message(response)

    # No debe contener términos técnicos
    assert "IntegrityError" not in message
    assert "database" not in message.lower()
    # Debe contener sugerencia
    assert "otras fechas" in message.lower()
```

**Estimación:** 2-3 días
**Valor:** Reduce abandono y confusión del usuario

---

### 5.2 Fotos de Alojamientos (2 días)

#### 🔥 Prioridad Alta - Confianza y conversión

**Características a Implementar:**

11. **Enviar Foto Principal al Consultar Disponibilidad**
    - Cuando usuario pregunta por alojamiento, enviar foto
    - Usar campo `photos` JSONB existente en modelo

    ```python
    # app/services/whatsapp.py
    async def send_accommodation_info_with_photo(
        phone: str,
        accommodation: Dict[str, Any]
    ):
        """Envía info de alojamiento con foto principal."""

        # Obtener URL de foto principal
        photos = accommodation.get('photos', [])
        main_photo_url = photos[0]['url'] if photos else None

        # Enviar foto si existe
        if main_photo_url:
            await send_whatsapp_image(
                phone=phone,
                image_url=main_photo_url,
                caption=f"📸 *{accommodation['name']}*"
            )

        # Luego enviar detalles
        message = f"""🏠 *{accommodation['name']}*

    📏 Capacidad: {accommodation['capacity']} personas
    💰 Precio base: ${accommodation['base_price']}/noche

    {accommodation['description']}

    ¿Te gustaría consultar disponibilidad para fechas específicas?"""

        await send_whatsapp_message(phone, message)

    async def send_whatsapp_image(phone: str, image_url: str, caption: str = ""):
        """Envía imagen por WhatsApp."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
                headers={
                    "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
    ```

**Schema de `photos` en DB (ya existe):**
```json
{
  "photos": [
    {
      "url": "https://example.com/photo1.jpg",
      "caption": "Vista exterior",
      "order": 0,
      "is_primary": true
    }
  ]
}
```

**Tests:**
```bash
# backend/tests/test_whatsapp_photos.py
async def test_send_accommodation_with_photo():
    """Debe enviar foto al mostrar info de alojamiento."""
    # Mock WhatsApp API
    # Consultar info de alojamiento
    # Verificar que se llamó endpoint de imagen
    # Verificar URL de foto en payload

async def test_send_accommodation_without_photo_works():
    """Debe funcionar aunque alojamiento no tenga foto."""
    # Crear alojamiento sin photos
    # Consultar info
    # Verificar que no falla
    # Verificar que envía texto igual
```

**Estimación:** 2 días
**Valor:** Aumenta confianza y tasa de conversión

---

### 5.3 Mensajes de Estado de Pago (1-2 días)

#### 🔥 Prioridad Alta - Transparencia en proceso de pago

**Características a Implementar:**

12. **Notificación Automática al Recibir Pago**
    - Cuando webhook de MP confirma pago, notificar por WhatsApp
    - Ya existe código base, agregar mensaje

    ```python
    # app/routers/mercadopago.py (mejorar webhook handler)
    @router.post("/webhooks/mercadopago")
    async def webhook_mercadopago(request: Request):
        # ... validación de firma ...

        if event_type == "payment" and action == "payment.created":
            payment_id = data.get("id")

            # Obtener detalles del pago
            payment = await mercadopago_service.get_payment(payment_id)

            if payment["status"] == "approved":
                # Actualizar reserva
                reservation = await update_reservation_payment_status(
                    external_reference=payment["external_reference"],
                    status="confirmed"
                )

                # 🔥 NUEVO: Notificar por WhatsApp
                if reservation and reservation.guest_phone:
                    await send_payment_confirmation(
                        phone=reservation.guest_phone,
                        reservation=reservation
                    )

        return {"status": "ok"}

    # app/services/whatsapp.py
    async def send_payment_confirmation(phone: str, reservation: Reservation):
        """Notifica confirmación de pago y reserva."""

        message = f"""🎉 *¡Pago Confirmado!*

    Tu reserva está confirmada:

    📋 Código: {reservation.code}
    🏠 {reservation.accommodation.name}
    📅 {reservation.check_in.strftime('%d/%m/%Y')} - {reservation.check_out.strftime('%d/%m/%Y')}
    ✅ Estado: CONFIRMADA

    Recibirás más detalles por email en breve.

    ¡Nos vemos pronto! 😊"""

        await send_whatsapp_message(phone, message)
    ```

**Tests:**
```bash
# backend/tests/test_payment_notifications.py
async def test_payment_webhook_sends_whatsapp_notification():
    """Webhook de pago aprobado debe notificar por WhatsApp."""
    # Crear pre-reserva con teléfono
    # Simular webhook MP con pago aprobado
    # Verificar mensaje WhatsApp enviado
    # Verificar contenido del mensaje

async def test_payment_notification_not_sent_if_rejected():
    """No debe notificar si pago es rechazado."""
    # Webhook con status=rejected
    # Verificar que NO se envió mensaje WhatsApp
```

**Estimación:** 1-2 días
**Valor:** Mejora UX y reduce ansiedad del usuario

---

## 📊 FASE 6: Robustez Operacional (1 semana)

### Objetivo
Garantizar que el sistema funcione 24/7 sin intervención manual.

---

### 6.1 Retry Logic en Integraciones (2-3 días)

#### 🔥 Prioridad Alta - Resiliencia ante fallos transitorios

**Características a Implementar:**

13. **Retry con Backoff Exponencial para WhatsApp API**
    - Reintentar envíos de mensajes fallidos
    - Backoff exponencial para no saturar

    ```python
    # app/services/whatsapp.py
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type
    )
    import httpx

    WHATSAPP_SEND_RETRIES = Counter(
        'whatsapp_send_retries_total',
        'Reintentos de envío WhatsApp',
        ['attempt']
    )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        before_sleep=lambda retry_state: WHATSAPP_SEND_RETRIES.labels(
            attempt=retry_state.attempt_number
        ).inc()
    )
    async def send_whatsapp_message_with_retry(
        phone: str,
        message: str
    ) -> Dict[str, Any]:
        """Envía mensaje WhatsApp con retry logic."""

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
                headers={
                    "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "text",
                    "text": {"body": message}
                }
            )

            # Si es 5xx o timeout, tenacity reintentará
            response.raise_for_status()
            return response.json()
    ```

14. **Circuit Breaker para Servicios Externos**
    - Evitar sobrecarga cuando servicio externo está caído
    - Fallar rápido después de N errores consecutivos

    ```python
    # app/core/circuit_breaker.py
    from datetime import datetime, timedelta
    from enum import Enum

    class CircuitState(Enum):
        CLOSED = "closed"  # Normal
        OPEN = "open"      # Fallando, rechazar requests
        HALF_OPEN = "half_open"  # Probando recuperación

    class CircuitBreaker:
        def __init__(
            self,
            failure_threshold: int = 5,
            timeout_seconds: int = 60,
            success_threshold: int = 2
        ):
            self.failure_threshold = failure_threshold
            self.timeout = timeout_seconds
            self.success_threshold = success_threshold

            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None

        async def call(self, func, *args, **kwargs):
            """Ejecuta función con circuit breaker."""

            # Si está OPEN, verificar si pasó timeout
            if self.state == CircuitState.OPEN:
                if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout):
                    logger.info("circuit_breaker_half_open")
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError("Circuit breaker is open")

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise

        def _on_success(self):
            """Maneja éxito de llamada."""
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info("circuit_breaker_closed")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            else:
                self.failure_count = 0

        def _on_failure(self):
            """Maneja fallo de llamada."""
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.failure_count >= self.failure_threshold:
                logger.warning(
                    "circuit_breaker_opened",
                    failure_count=self.failure_count
                )
                self.state = CircuitState.OPEN

    # Uso
    whatsapp_circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        timeout_seconds=60
    )

    async def send_whatsapp_message(phone: str, message: str):
        """Envía mensaje con circuit breaker."""
        return await whatsapp_circuit_breaker.call(
            send_whatsapp_message_with_retry,
            phone,
            message
        )
    ```

**Tests:**
```bash
# backend/tests/test_resilience.py
async def test_retry_on_timeout():
    """Debe reintentar en timeout."""
    # Mock WhatsApp API con timeout
    # Verificar 3 intentos
    # Verificar backoff exponencial

async def test_circuit_breaker_opens_after_failures():
    """Circuit breaker debe abrirse tras N fallos."""
    # Causar 5 fallos consecutivos
    # Verificar que siguiente llamada falla inmediatamente
    # No debe llamar a API externa

async def test_circuit_breaker_recovers():
    """Circuit breaker debe recuperarse tras timeout."""
    # Abrir circuit breaker
    # Esperar timeout
    # Hacer 2 llamadas exitosas
    # Verificar que vuelve a CLOSED
```

**Estimación:** 2-3 días
**Valor:** Evita cascadas de fallos y mejora disponibilidad

---

### 6.2 Idempotencia Completa (2 días)

#### 🔥 Prioridad Alta - Evitar procesamiento duplicado

**Características a Implementar:**

15. **Idempotency Key en Webhooks**
    - Detectar y rechazar webhooks duplicados
    - Usar Redis para tracking

    ```python
    # app/core/idempotency.py
    from hashlib import sha256

    async def check_idempotency(
        redis_pool,
        idempotency_key: str,
        ttl_seconds: int = 86400  # 24 horas
    ) -> bool:
        """Verifica si operación ya fue procesada."""

        redis_conn = redis_pool.client()
        key = f"idempotency:{idempotency_key}"

        # Intentar setear key (solo funciona si no existe)
        was_set = await redis_conn.set(key, "1", nx=True, ex=ttl_seconds)
        return was_set  # True = primera vez, False = duplicado

    # app/routers/webhooks.py
    @router.post("/webhooks/whatsapp")
    async def webhook_whatsapp(request: Request):
        payload = await request.json()

        # Generar idempotency key único del mensaje
        message_id = extract_message_id(payload)
        if message_id:
            idempotency_key = f"whatsapp:{message_id}"

            # Verificar si ya procesamos este mensaje
            is_new = await check_idempotency(
                await get_redis_pool(),
                idempotency_key
            )

            if not is_new:
                logger.info(
                    "webhook_duplicate_ignored",
                    message_id=message_id
                )
                return {"status": "ok"}  # Responder OK pero no procesar

        # Procesar mensaje normalmente
        await process_whatsapp_message(payload)
        return {"status": "ok"}
    ```

**Tests:**
```bash
# backend/tests/test_idempotency.py
async def test_duplicate_webhook_ignored():
    """Webhook duplicado no debe procesarse dos veces."""
    payload = generate_whatsapp_webhook_payload()

    # Primer envío
    response1 = await client.post("/api/v1/webhooks/whatsapp", json=payload)
    assert response1.status_code == 200

    # Segundo envío (duplicado)
    response2 = await client.post("/api/v1/webhooks/whatsapp", json=payload)
    assert response2.status_code == 200

    # Verificar que solo se procesó una vez
    messages = await get_processed_messages()
    assert len(messages) == 1
```

**Estimación:** 2 días
**Valor:** Evita doble procesamiento y bugs sutiles

---

## 📅 Timeline Consolidado

```
SEMANA 1-2: Fase 4 - Optimización y Robustez
├─ Días 1-4: Background jobs + Health checks
├─ Días 5-7: Rate limiting + Logging estructurado
└─ Días 8-10: Buffer y ajustes

SEMANA 3: Fase 5 - Quick Wins UX
├─ Días 11-13: Mensajes confirmación + errores amigables
├─ Días 14-15: Fotos de alojamientos
└─ Días 16-17: Notificaciones de pago

SEMANA 4: Fase 6 - Robustez Operacional
├─ Días 18-20: Retry logic + Circuit breaker
├─ Días 21-22: Idempotencia completa
└─ Días 23-24: Testing integral + docs

TOTAL: 3-4 semanas
```

---

## ✅ Checklist de Aceptación MVP

### Antes de Producción

- [ ] **Observabilidad**
  - [ ] Métricas Prometheus expuestas en `/metrics`
  - [ ] Health check responde correctamente en `/api/v1/healthz`
  - [ ] Logs JSON estructurados con trace_id
  - [ ] Alertas configuradas para errores críticos

- [ ] **Robustez**
  - [ ] Background jobs funcionan (expiración + iCal sync)
  - [ ] Rate limiting activo en webhooks públicos
  - [ ] Retry logic en llamadas a WhatsApp API
  - [ ] Circuit breaker protege contra cascadas de fallos
  - [ ] Idempotencia en webhooks (sin duplicados)

- [ ] **UX**
  - [ ] Mensajes de confirmación con todos los detalles
  - [ ] Errores amigables con sugerencias
  - [ ] Fotos de alojamientos se envían correctamente
  - [ ] Notificaciones automáticas de pago

- [ ] **Testing**
  - [ ] Tests unitarios pasan (>80% cobertura core)
  - [ ] Tests de integración pasan (webhooks, pagos, audio)
  - [ ] Tests E2E pasan (flujo completo reserva)
  - [ ] Tests de resiliencia pasan (retry, circuit breaker)

- [ ] **Documentación**
  - [ ] README actualizado con setup completo
  - [ ] Runbook con procedimientos de operación
  - [ ] Diagramas de arquitectura actualizados

---

## 🚫 Fuera del Scope MVP

Las siguientes características se evaluarán **DESPUÉS** del MVP en producción con usuarios reales:

### NO Implementar (Post-MVP)
- ❌ Botones interactivos WhatsApp (complejidad vs valor bajo)
- ❌ Recordatorios automáticos (no crítico para booking)
- ❌ Multi-idioma (99% usuarios español argentino)
- ❌ Contexto conversacional Redis FSM (over-engineering para MVP)
- ❌ Personalización de clientes recurrentes (feature avanzada)
- ❌ Servicios adicionales/extras (complejidad innecesaria)
- ❌ Check-in digital (requiere integración compleja)
- ❌ Recomendaciones ML (no hay datos suficientes)
- ❌ Integración Google Places/Maps (nice-to-have)
- ❌ Grafana dashboards (Prometheus + logs suficiente para MVP)

---

## 🎯 Métricas de Éxito MVP

### Técnicas
- **Uptime:** >99.5% (medido por health checks)
- **P95 Latency Texto:** <3s
- **P95 Latency Audio:** <15s
- **Error Rate:** <1%
- **iCal Sync Desfase:** <20min

### Negocio
- **Tasa de Conversión Pre-reserva:** >30%
- **Tasa de Confirmación (Pago):** >60%
- **Tiempo Respuesta Promedio:** <30s
- **Doble-Bookings:** 0 (crítico)

### Operacionales
- **Intervenciones Manuales:** <5/semana
- **Tiempo Resolución Incidentes:** <2h
- **False Positives Rate Limit:** <0.1%

---

## 📝 Siguiente Paso Inmediato

1. **Revisar y Aprobar este Roadmap** ✋
   - Confirmar prioridades
   - Ajustar tiempos si es necesario
   - Decidir orden de implementación

2. **Comenzar con Fase 4.1** (Background Jobs)
   - Es la base para observabilidad
   - Quick win: ya existe código base
   - Bloquea otros features

3. **Setup de Monitoreo**
   - Configurar Prometheus scraping
   - Configurar logs centralizados
   - Setup alertas básicas (uptime, error rate)

---

## 💡 Filosofía de Implementación

### Reglas de Oro
1. **SHIPPING > PERFECCIÓN** - Priorizar funcionalidad sobre elegancia
2. **Tests Verdes = Deploy** - No refactorizar si los tests pasan
3. **MÁS SIMPLE = Mejor** - Evitar abstracciones innecesarias
4. **Observabilidad es Feature** - Si no se puede medir, no existe
5. **Fail Fast** - Detectar errores rápido, recuperarse rápido

### Anti-Patrones Prohibidos
- ❌ "Sería fácil agregar..." → STOP
- ❌ "Por completitud..." → STOP
- ❌ "Ya que estamos..." → STOP
- ❌ Cache sin evidencia → STOP
- ❌ Abstracciones "por si acaso" → STOP

---

**¿Aprobamos este plan y comenzamos con Fase 4?** 🚀
