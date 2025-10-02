# Troubleshooting & FAQ - Sistema MVP Alojamientos

**Versión:** 0.9.8
**Última actualización:** 2025-10-02

---

## 📋 Tabla de Contenidos

- [Problemas Comunes](#problemas-comunes)
- [Doble-Booking](#doble-booking)
- [Webhooks](#webhooks)
- [Base de Datos](#base-de-datos)
- [Redis](#redis)
- [iCal Sync](#ical-sync)
- [Performance](#performance)
- [Deployment](#deployment)
- [Logs & Debug](#logs--debug)
- [FAQ](#faq)

---

## Problemas Comunes

### 🔴 "Tests Fallan al Ejecutar"

**Síntoma:**
```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**Causa:** Virtual environment no activado

**Solución:**
```bash
cd backend
source ../.venv/bin/activate  # Linux/Mac
# o
..\\.venv\\Scripts\\activate  # Windows

pytest tests/ -v
```

**Prevención:** Siempre verificar `(venv)` en prompt antes de ejecutar tests

---

### 🔴 "Pre-commit Hooks Fallan"

**Síntoma:**
```
[ERROR] pre-commit not installed
```

**Causa:** pre-commit no instalado en el sistema

**Solución:**
```bash
pip install pre-commit
pre-commit install
```

**Verificación:**
```bash
pre-commit run --all-files
```

---

### 🔴 "Docker Compose No Levanta"

**Síntoma:**
```
Error: port 5432 already in use
```

**Causa:** PostgreSQL/Redis ya corriendo en host

**Solución 1 (Detener servicios locales):**
```bash
sudo systemctl stop postgresql
sudo systemctl stop redis
docker-compose up -d
```

**Solución 2 (Cambiar puertos):**
```yaml
# docker-compose.yml
services:
  postgres:
    ports:
      - "5433:5432"  # Cambiar puerto externo
```

---

## Doble-Booking

### 🔴 "Reserva Doble a Pesar del Constraint"

**Síntoma:** Dos reservas con fechas solapadas en la misma accommodation

**Diagnóstico:**
```sql
-- Verificar constraint existe
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'reservations'::regclass
  AND conname = 'no_overlap_reservations';

-- Verificar extensión btree_gist
SELECT * FROM pg_extension WHERE extname = 'btree_gist';

-- Buscar overlaps
SELECT r1.code, r1.check_in, r1.check_out, r1.reservation_status,
       r2.code, r2.check_in, r2.check_out, r2.reservation_status
FROM reservations r1
JOIN reservations r2 ON r1.accommodation_id = r2.accommodation_id
  AND r1.id < r2.id
  AND daterange(r1.check_in, r1.check_out, '[)') &&
      daterange(r2.check_in, r2.check_out, '[)')
WHERE r1.reservation_status IN ('pre_reserved', 'confirmed')
  AND r2.reservation_status IN ('pre_reserved', 'confirmed');
```

**Causas Posibles:**

1. **Extensión btree_gist no creada:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS btree_gist;
   ```

2. **Constraint no aplicado:**
   ```sql
   ALTER TABLE reservations
     ADD CONSTRAINT no_overlap_reservations
     EXCLUDE USING gist (
       accommodation_id WITH =,
       period WITH &&
     )
     WHERE (reservation_status IN ('pre_reserved', 'confirmed'));
   ```

3. **Reservas en estado 'cancelled' o 'expired':**
   - Esperado: constraint solo aplica a `pre_reserved` y `confirmed`
   - Verificar: `WHERE reservation_status IN (...)`

**Prevención:**
- Ejecutar `backend/tests/test_double_booking.py` regularmente
- Monitorear constraint violations en logs

---

### 🟡 "Lock Redis No Se Libera"

**Síntoma:** No se pueden crear reservas para fechas específicas

**Diagnóstico:**
```bash
# Conectar a Redis
docker-compose exec redis redis-cli

# Listar locks
KEYS lock:acc:*

# Ver TTL de un lock
TTL lock:acc:1:2024-09-20:2024-09-22

# Ver valor
GET lock:acc:1:2024-09-20:2024-09-22
```

**Solución 1 (Lock expirado naturalmente):**
- TTL es 1800s (30 min). Esperar expiración automática

**Solución 2 (Limpiar lock manualmente):**
```bash
# SOLO EN DESARROLLO
redis-cli DEL lock:acc:1:2024-09-20:2024-09-22
```

**⚠️ Advertencia:** NO borrar locks en producción sin verificar que no hay request activo

**Prevención:**
- Implementar `finally` block para liberar locks en código
- Monitorear keys con TTL > 1800s (anomalía)

---

## Webhooks

### 🔴 "WhatsApp Webhook Retorna 403"

**Síntoma:**
```json
{
  "error": "invalid_signature",
  "message": "Webhook signature validation failed"
}
```

**Causa:** Firma HMAC inválida o `WHATSAPP_APP_SECRET` incorrecto

**Diagnóstico:**
```python
# En logs buscar:
# "Invalid WhatsApp signature" o "Missing X-Hub-Signature-256"

# Verificar secret configurado
echo $WHATSAPP_APP_SECRET

# Test manual de firma
python -c "
import hmac, hashlib
payload = b'{\"test\":\"data\"}'
secret = 'TU_SECRET'
signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
print(f'sha256={signature}')
"
```

**Solución:**
1. Verificar `WHATSAPP_APP_SECRET` en `.env` coincide con Meta Developer Console
2. Verificar header `X-Hub-Signature-256` en request
3. Verificar payload exacto (sin modificar espacios/encoding)

**Testing:**
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/whatsapp \
  -H "X-Hub-Signature-256: sha256=FIRMA_CORRECTA" \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'
```

---

### 🔴 "Mercado Pago Webhook Retorna 403"

**Síntoma:** Pagos no se procesan, webhook falla

**Diagnóstico:**
```python
# Verificar logs
docker-compose logs -f api | grep "mercadopago"

# Verificar secret
echo $MERCADOPAGO_WEBHOOK_SECRET

# Test manual
python -c "
import hmac, hashlib
data_id = '12345678'
request_id = 'abc123'
ts = '1695042000'
secret = 'TU_SECRET'
manifest = f'id:{data_id};request-id:{request_id};ts:{ts};'
signature = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
print(f'ts={ts},v1={signature}')
"
```

**Solución:**
1. Obtener `MERCADOPAGO_WEBHOOK_SECRET` desde MP Developer Dashboard
2. Verificar header `x-signature` formato: `ts=X,v1=Y`
3. Verificar timestamp no es muy antiguo (>5 min = posible replay attack)

**Idempotencia:**
- Si webhook se reintenta, sistema debe manejar duplicados por `payment_id`
- Verificar logs: "Payment already processed" (esperado)

---

### 🟡 "Audio Transcription Falla"

**Síntoma:**
```json
{
  "error": "audio_unclear",
  "message": "Audio confidence too low"
}
```

**Causa:** Whisper confidence < 0.6

**Diagnóstico:**
```python
# Ver logs de transcripción
docker-compose logs -f api | grep "audio"

# Buscar:
# "Audio transcription completed" (success)
# "Low confidence transcription" (failure)
# confidence_score: 0.45  # < 0.6
```

**Solución para Usuario:**
- Responder automáticamente: "Audio poco claro, por favor repite en texto"

**Solución Técnica:**
1. Verificar audio_url descarga correctamente
2. Verificar conversión FFmpeg funciona: `ffmpeg -i input.ogg output.wav`
3. Ajustar threshold si muchos falsos negativos: `WHISPER_CONFIDENCE_THRESHOLD=0.5`

**Mejoras Futuras:**
- Modelo Whisper más grande (`medium` vs `base`)
- Noise reduction con FFmpeg antes de STT

---

## Base de Datos

### 🔴 "Connection Pool Exhausted"

**Síntoma:**
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size X overflow Y reached
```

**Causa:** Demasiadas conexiones concurrentes

**Diagnóstico:**
```sql
-- Ver conexiones activas
SELECT count(*) FROM pg_stat_activity
WHERE datname = 'alojamientos_db';

-- Ver por estado
SELECT state, count(*) FROM pg_stat_activity
WHERE datname = 'alojamientos_db'
GROUP BY state;
```

**Solución Inmediata:**
```sql
-- Terminar conexiones idle (CUIDADO en producción)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'alojamientos_db'
  AND state = 'idle'
  AND state_change < now() - interval '10 minutes';
```

**Solución Permanente:**
```python
# app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Aumentar de 10 a 20
    max_overflow=10,     # Pool adicional
    pool_pre_ping=True,  # Verificar conexiones
    pool_recycle=3600    # Reciclar cada hora
)
```

**Prevención:**
- Monitorear `pg_stat_activity` periódicamente
- Usar connection pooling externo (PgBouncer) en producción

---

### 🔴 "Migraciones Alembic Fallan"

**Síntoma:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Diagnóstico:**
```bash
# Ver estado actual
docker-compose exec api alembic current

# Ver historial
docker-compose exec api alembic history

# Ver head esperado
docker-compose exec api alembic heads
```

**Solución (Base limpia):**
```bash
# 1. Backup de datos
make backup

# 2. Drop y recrear DB
make db-reset  # CUIDADO: Borra todos los datos

# 3. Ejecutar migraciones
docker-compose exec api alembic upgrade head
```

**Solución (Reparar historial):**
```bash
# Stamp actual como base
docker-compose exec api alembic stamp head

# Ejecutar migraciones faltantes
docker-compose exec api alembic upgrade head
```

---

## Redis

### 🔴 "Redis Connection Refused"

**Síntoma:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Diagnóstico:**
```bash
# Verificar Redis corriendo
docker-compose ps redis

# Logs Redis
docker-compose logs redis

# Test conexión
docker-compose exec redis redis-cli PING
# Esperado: PONG
```

**Solución:**
```bash
# Reiniciar Redis
docker-compose restart redis

# Verificar health
docker-compose exec redis redis-cli INFO server
```

**Fail-Safe:** Sistema debe funcionar sin Redis (rate limit se desactiva automáticamente)

---

### 🟡 "Rate Limit No Funciona"

**Síntoma:** Requests no son limitados

**Diagnóstico:**
```python
# Ver logs de rate limit
docker-compose logs -f api | grep "rate_limit"

# Verificar Redis tiene keys
docker-compose exec redis redis-cli KEYS rate_limit:*

# Ver valor de una key
docker-compose exec redis redis-cli GET rate_limit:127.0.0.1:/api/v1/reservations
```

**Causa:** Redis caído → fail-open (esperado)

**Solución:** Levantar Redis si es necesario limitar

**Verificación:**
```bash
# Test rate limit
for i in {1..65}; do
  curl http://localhost:8000/api/v1/healthz
done
# Request 61+ debe retornar 429
```

---

## iCal Sync

### 🔴 "iCal No Sincroniza"

**Síntoma:** Reservas externas no aparecen en sistema

**Diagnóstico:**
```bash
# Ver logs de sync job
docker-compose logs -f api | grep "ical"

# Ver métricas
curl http://localhost:8000/metrics | grep ical_last_sync

# Verificar edad último sync
curl http://localhost:8000/api/v1/healthz | jq '.checks.ical_sync'
```

**Causas Posibles:**

1. **URL iCal inválida:**
   ```sql
   SELECT id, name, ical_url FROM accommodations;
   -- Verificar URLs son válidas
   ```

2. **Job scheduler no corriendo:**
   ```bash
   # Ver logs de scheduler
   docker-compose logs api | grep "scheduler"
   # Debe ver: "iCal sync job started"
   ```

3. **Errores de parsing:**
   ```python
   # Buscar en logs:
   # "Invalid iCal format" o "Failed to parse VEVENT"
   ```

**Solución:**
```bash
# Trigger sync manual (future endpoint)
curl -X POST http://localhost:8000/api/v1/admin/ical/sync-now

# Verificar métricas después
curl http://localhost:8000/metrics | grep ical_last_sync_age_minutes
```

---

### 🟡 "Duplicados en iCal Import"

**Síntoma:** Misma reserva importada múltiples veces

**Diagnóstico:**
```sql
-- Buscar duplicados por UID
SELECT uid, count(*)
FROM reservations
WHERE channel_source = 'ical_import'
GROUP BY uid
HAVING count(*) > 1;

-- Buscar duplicados por fechas
SELECT accommodation_id, check_in, check_out, count(*)
FROM reservations
WHERE channel_source = 'ical_import'
GROUP BY accommodation_id, check_in, check_out
HAVING count(*) > 1;
```

**Causa:** Lógica de deduplicación falló

**Solución:**
```sql
-- Eliminar duplicados (CUIDADO)
DELETE FROM reservations r1
WHERE r1.channel_source = 'ical_import'
  AND EXISTS (
    SELECT 1 FROM reservations r2
    WHERE r2.uid = r1.uid
      AND r2.id < r1.id  -- Mantener el más antiguo
  );
```

**Prevención:**
- Verificar test `test_import_ical_dedup` pasa
- Revisar lógica en `services/ical.py::import_ical()`

---

## Performance

### 🟡 "API Lenta (>3s)"

**Síntoma:** Health check reporta warning, P95 > 3s

**Diagnóstico:**
```bash
# Ver métricas
curl http://localhost:8000/metrics | grep http_request_duration

# Ver logs con latencias
docker-compose logs api | grep "duration_ms"
```

**Causas Comunes:**

1. **Query DB lenta:**
   ```sql
   -- Ver queries lentas
   SELECT query, calls, mean_exec_time, max_exec_time
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

2. **N+1 queries:**
   - Buscar en código: `for accommodation in accommodations: get_reservations(accommodation.id)`
   - Usar `joinedload` en SQLAlchemy

3. **Redis lento:**
   ```bash
   docker-compose exec redis redis-cli --latency
   # Debe ser < 1ms
   ```

**Solución:**
```python
# Agregar índices DB
CREATE INDEX idx_reservations_dates ON reservations(check_in, check_out);
CREATE INDEX idx_reservations_status ON reservations(reservation_status);

# Usar eager loading
accommodations = session.execute(
    select(Accommodation).options(joinedload(Accommodation.reservations))
).scalars().all()
```

---

## Deployment

### 🔴 "Deploy Falla en Pre-checks"

**Síntoma:** `scripts/pre-deploy-check.sh` retorna error

**Diagnóstico:**
```bash
# Ejecutar con verbose
bash -x scripts/pre-deploy-check.sh
```

**Checklist:**
- [ ] `.env` tiene todas las variables (compara con `.env.template`)
- [ ] Tests pasan: `pytest tests/ -v`
- [ ] Docker Compose válido: `docker-compose config`
- [ ] Nginx template válido: `nginx -t -c nginx.conf`

**Solución por Check:**

1. **Tests fallan:** Arreglar tests antes de deploy
2. **Variables faltantes:** Completar `.env`
3. **Docker inválido:** Verificar sintaxis YAML
4. **Nginx inválido:** Verificar `server_name`, `ssl_certificate`

---

### 🔴 "Smoke Tests Fallan en Producción"

**Síntoma:** `scripts/smoke-test-prod.sh` retorna errores

**Diagnóstico:**
```bash
# Ejecutar con verbose
DOMAIN=tu-dominio.com bash -x scripts/smoke-test-prod.sh
```

**Tests Críticos:**

1. **Health check unhealthy:**
   - Verificar DB/Redis accesibles desde container
   - Verificar variables de entorno correctas

2. **Prometheus metrics no responden:**
   - Verificar `/metrics` expuesto
   - Verificar Nginx proxy_pass correcto

3. **Reservations API falla:**
   - Verificar DB migrations ejecutadas: `alembic current`
   - Verificar constraints DB: `\d reservations` en psql

---

## Logs & Debug

### 📋 "Cómo Ver Logs Estructurados"

**Logs en JSON:**
```bash
# Ver logs con jq
docker-compose logs api -f | jq

# Filtrar por nivel
docker-compose logs api -f | jq 'select(.level=="ERROR")'

# Filtrar por trace_id
docker-compose logs api -f | jq 'select(.trace_id=="abc123")'

# Buscar errores de reservación
docker-compose logs api -f | jq 'select(.event | contains("reservation"))'
```

**Métricas útiles:**
```bash
# Reservations creadas
curl -s localhost:8000/metrics | grep reservations_created_total

# Latencias API
curl -s localhost:8000/metrics | grep http_request_duration_seconds

# Edad sync iCal
curl -s localhost:8000/metrics | grep ical_last_sync_age_minutes
```

---

### 🔍 "Debug Request Específico"

**Con trace_id:**
```bash
# Logs de un request específico
docker-compose logs api | grep "trace_id=abc123"
```

**Sin trace_id (usar timestamp):**
```bash
# Logs alrededor de un timestamp
docker-compose logs api --since "2024-09-15T12:00:00" --until "2024-09-15T12:05:00"
```

---

## FAQ

### ❓ ¿Cómo resetear la base de datos en desarrollo?

```bash
make db-reset
# O manualmente:
docker-compose down -v
docker-compose up -d postgres redis
sleep 5
docker-compose exec api alembic upgrade head
```

⚠️ **CUIDADO:** Esto borra TODOS los datos.

---

### ❓ ¿Cómo probar webhooks localmente?

**Opción 1: ngrok**
```bash
ngrok http 8000
# Copiar URL https://xyz.ngrok.io
# Configurar en Meta/MP Dashboard
```

**Opción 2: Webhook.site**
- Usar https://webhook.site para capturar payloads
- Copiar payload y replayar localmente

**Opción 3: Mock requests**
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/whatsapp \
  -H "X-Hub-Signature-256: sha256=$(echo -n 'payload' | openssl dgst -sha256 -hmac 'secret' | cut -d' ' -f2)" \
  -d '{"test":"data"}'
```

---

### ❓ ¿Cómo agregar un nuevo alojamiento?

**Por SQL (desarrollo):**
```sql
INSERT INTO accommodations (
  name, type, capacity, base_price, description,
  amenities, photos, location, policies, active
) VALUES (
  'Nueva Cabaña', 'cabin', 4, 5000.00, 'Descripción',
  '["wifi", "pool"]'::jsonb,
  '[]'::jsonb,
  '{"address": "Calle 123"}'::jsonb,
  '{"check_in": "14:00", "check_out": "10:00"}'::jsonb,
  true
);
```

**Por Admin API (future):**
```bash
curl -X POST http://localhost:8000/api/v1/admin/accommodations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Nueva Cabaña", ...}'
```

---

### ❓ ¿Cómo exportar métricas a Prometheus?

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'alojamientos-mvp'
    static_configs:
      - targets: ['api.alojamientos.example.com']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Verificar:**
```bash
curl http://localhost:8000/metrics
```

---

### ❓ ¿Cómo escalar horizontalmente?

**Docker Swarm:**
```bash
docker service scale alojamientos_api=3
```

**Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alojamientos-api
spec:
  replicas: 3
  # ...
```

**Load Balancer:**
- Nginx upstream con múltiples backends
- Redis garantiza locks distribuidos entre instancias

---

### ❓ ¿Cómo hacer backup de la base de datos?

**Manual:**
```bash
make backup
# O:
docker-compose exec -T postgres pg_dump -U alojamientos alojamientos_db > backup.sql
```

**Automatizado (cron):**
```bash
# /etc/cron.d/alojamientos-backup
0 2 * * * cd /app && make backup && aws s3 cp backup_*.sql s3://backups/
```

**Restore:**
```bash
make restore FILE=backup_20241002_120000.sql
```

---

### ❓ ¿Qué hacer si hay un doble-booking en producción?

1. **Confirmar overlap:**
   ```sql
   SELECT * FROM reservations
   WHERE accommodation_id = X
     AND daterange(check_in, check_out, '[)') &&
         daterange('2024-09-20', '2024-09-22', '[)')
     AND reservation_status IN ('pre_reserved', 'confirmed');
   ```

2. **Contactar huéspedes afectados inmediatamente**

3. **Opciones:**
   - Ofrecer alojamiento alternativo
   - Reembolso + compensación
   - Upgrade gratuito

4. **Investigar causa raíz:**
   - Revisar logs: `docker-compose logs api | grep "IntegrityError"`
   - Verificar constraint: `\d reservations`
   - Verificar locks Redis

5. **Crear incident report y ADR**

---

## 🆘 Soporte

### Canales de Ayuda

1. **Documentación:**
   - [README.md](../README.md)
   - [CONTRIBUTING.md](../CONTRIBUTING.md)
   - [TECHNICAL_ARCHITECTURE.md](./architecture/TECHNICAL_ARCHITECTURE.md)
   - [API_REFERENCE.md](./API_REFERENCE.md)

2. **GitHub Issues:**
   - [Reportar bug](https://github.com/eevans-d/SIST_CABANAS_MVP/issues/new?template=bug_report.md)
   - [Solicitar feature](https://github.com/eevans-d/SIST_CABANAS_MVP/issues/new?template=feature_request.md)

3. **Logs:**
   - `docker-compose logs -f api`
   - `/var/log/nginx/error.log`
   - Health checks: `/api/v1/healthz`

---

**Recuerda:** Ante dudas, consulta primero la documentación y los logs. Si el problema persiste, abre un issue con:
- Descripción del problema
- Steps to reproduce
- Logs relevantes
- Versión del sistema

---

**Última actualización:** 2025-10-02
**Mantenido por:** Sistema MVP Alojamientos Team
