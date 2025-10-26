# Incident Response Runbook

> **Audiencia:** On-call engineer, DevOps
> **Objetivo:** Pasos rápidos para diagnosticar y resolver incidentes críticos
> **Tiempo:** cada incidente < 10 min diagnosis, < 30 min resolución o rollback

---

## Alerta: Error Rate > 5% (CRITICAL)

### Síntomas
- Prometheus alert: `error_rate_high`
- Dashboard: líneas rojas en /errors

### Diagnosis (2 min)

```bash
# 1. Ver últimos errores
curl -s https://tu-dominio.com/api/v1/healthz | python -m json.tool

# 2. Ver logs (últimas 50 líneas)
flyctl logs -a sist-cabanas-prod --lines 50 | grep -i error

# 3. Buscar patrón de error
flyctl logs -a sist-cabanas-prod | grep -E "(500|exception|critical)" | tail -20
```

### Causas Comunes

| Causa | Síntomas | Fix |
|-------|----------|-----|
| DB down | `ERROR: connection refused` | Verificar Fly Postgres; restart si locked |
| Redis down | `ERROR: redis timeout` | Verificar Upstash; check REDIS_URL en secrets |
| Memory leak | `OOMKilled` en logs; error_rate crecer | Restart pod; analizardump heap después |
| Webhook loop | Req/s triple; 429 Too Many Requests | Kill webhook source; review webhook code |
| Config error | `ValueError: ...` en startup | Rollback a release anterior |

### Resolución Rápida

**Opción 1: Restart (si es glitch)**
```bash
flyctl restart -a sist-cabanas-prod
sleep 10
curl https://tu-dominio.com/api/v1/healthz
```

**Opción 2: Rollback (si es código)**
```bash
flyctl releases -a sist-cabanas-prod | head -5
flyctl releases rollback -a sist-cabanas-prod
sleep 20
# Verificar
curl https://tu-dominio.com/api/v1/healthz
```

**Opción 3: Scale up (si es carga)**
```bash
# Aumentar VMs de 1 a 2
flyctl scale count 2 -a sist-cabanas-prod
sleep 30
# Monitorear error_rate
```

---

## Alerta: Response Time p95 > 6s (WARNING)

### Diagnosis

```bash
# 1. Endpoint lento
curl -w "\nTime: %{time_total}s\n" -s https://tu-dominio.com/api/v1/reservations

# 2. DB latency
# Conectar a Fly Postgres y correr:
SELECT pg_sleep(5);  -- dummy query para ver latencia

# 3. Redis latency
redis-cli -u $REDIS_URL ping
```

### Causas Comunes

| Causa | Síntoma | Fix |
|-------|---------|-----|
| DB bajo carga | `SELECT` > 1s | Indexar table; kill long queries |
| Redis down | timeout | Reintentar; check REDIS_URL |
| N+1 query | requests endpoints → 100+ queries | Code fix; revert a versión anterior |
| Webhook procesando | webhook endpoint lento | Background job queue?; async/await check |

### Resolución

1. **Indexar rápido** (si es BD)
   ```bash
   # Conectar a Fly Postgres
   CREATE INDEX IF NOT EXISTS idx_reservations_check_in ON reservations(check_in);
   CREATE INDEX IF NOT EXISTS idx_accommodations_id ON accommodations(id);
   ```

2. **Cache en Redis** (si es lookup repetitivo)
   - Implementar TTL en Redis para accommodations
   - Refresco cada 15 min

3. **Rollback si es código**
   ```bash
   flyctl releases rollback -a sist-cabanas-prod
   ```

---

## Alerta: DB Connection Refused (CRITICAL)

### Diagnosis

```bash
# 1. Check DATABASE_URL secret
flyctl secrets list -a sist-cabanas-prod | grep DATABASE_URL

# 2. Check Fly Postgres status
flyctl postgres status -a sist-cabanas-db

# 3. Check logs para error específico
flyctl logs -a sist-cabanas-prod | grep -i database
```

### Resolución

1. **Fly Postgres parado?**
   ```bash
   flyctl postgres restart -a sist-cabanas-db
   sleep 60  # Esperar
   curl https://tu-dominio.com/api/v1/healthz
   ```

2. **DNS/red problem?**
   ```bash
   # Restart backend
   flyctl restart -a sist-cabanas-prod
   ```

3. **Connection pool exhausted?**
   - Aumentar `SQLALCHEMY_POOL_SIZE` (enviroment var)
   - O reducir conexiones de background jobs (JOB_* intervals)

---

## Alerta: Memory Usage > 90% (WARNING)

### Diagnosis

```bash
# Ver consumo en Fly dashboard
flyctl scale show -a sist-cabanas-prod

# O en logs
flyctl logs -a sist-cabanas-prod | grep -i memory
```

### Resolución

1. **Restart pod**
   ```bash
   flyctl restart -a sist-cabanas-prod
   ```

2. **Scale up VM**
   ```bash
   # Cambiar shared-cpu-1x → shared-cpu-2x o dedicated-cpu-1x
   flyctl scale vm shared-cpu-2x -a sist-cabanas-prod
   ```

3. **Encontrar leak**
   ```bash
   # Profiler en código (próxima versión)
   # Por ahora: monitor trends en dashboard
   ```

---

## Alerta: Webhook (WhatsApp/MP) Failing (WARNING)

### Diagnosis

```bash
# Ver logs de webhook
flyctl logs -a sist-cabanas-prod | grep -i webhook

# Check signature validation
flyctl logs -a sist-cabanas-prod | grep "invalid.*signature"
```

### Causas Comunes

| Webhook | Causa | Fix |
|---------|-------|-----|
| WhatsApp | Invalid signature | Verificar WHATSAPP_APP_SECRET en secrets |
| WhatsApp | Endpoint no responde 200 | Check logs; `flyctl restart` si hung |
| Mercado Pago | Duplicate payment | Idempotency key no aplicada; check code |
| Mercado Pago | Secret mismatch | Verify MERCADOPAGO_WEBHOOK_SECRET en secrets |

### Resolución

1. **Validar secret**
   ```bash
   flyctl secrets list -a sist-cabanas-prod | grep WHATSAPP_APP_SECRET
   # Si vacío o malo: actualizar
   flyctl secrets set WHATSAPP_APP_SECRET="nuevo_valor" -a sist-cabanas-prod
   # Restart
   flyctl restart -a sist-cabanas-prod
   ```

2. **Replay webhook manualmente** (desde proveedor)
   - WhatsApp: Dashboard → Message Logs → resend
   - MP: Dashboard → Webhooks → manual trigger

---

## Alerta: iCal Sync Desfased > 30 min (WARNING)

### Diagnosis

```bash
# Ver métrica en Prometheus
# ical_last_sync_age_minutes > 30

# O check en logs
flyctl logs -a sist-cabanas-prod | grep -i ical
```

### Causas Comunes

| Causa | Fix |
|-------|-----|
| Background job no corre | Restart pod |
| Airbnb/Booking URL down | Manual refresh (próxima versión) |
| iCal parser error | Check logs; report bug |

### Resolución

1. **Trigger manual sync**
   ```bash
   # POST /api/v1/ical/sync (endpoint admin, requiere JWT)
   curl -X POST https://tu-dominio.com/api/v1/ical/sync \
     -H "Authorization: Bearer <admin-token>" \
     -H "Content-Type: application/json"
   ```

2. **Check job en código**
   - Archivo: `backend/jobs/import_ical.py`
   - Interval: `JOB_ICAL_INTERVAL_SECONDS` (default 300s)

3. **Si url de iCal rota o cambia**
   - Actualizar manualmente en `accommodations.ical_url`
   - O retraso: esperar siguiente sync

---

## Alerta: Double-Booking Detected (CRITICAL)

> Nota: Esto NO debería pasar si EXCLUDE gist constraint está activo.

### Diagnosis

```bash
# 1. Ver reserva problemática
flyctl postgres connect sist-cabanas-db
SELECT id, accommodation_id, check_in, check_out, reservation_status
FROM reservations
WHERE accommodation_id = 1
ORDER BY created_at DESC
LIMIT 10;

# 2. Buscar solapes
SELECT a.id, a.check_in, a.check_out, b.id, b.check_in, b.check_out
FROM reservations a, reservations b
WHERE a.accommodation_id = b.accommodation_id
  AND a.id < b.id
  AND a.reservation_status = 'confirmed'
  AND b.reservation_status = 'confirmed'
  AND daterange(a.check_in, a.check_out, '[)') && daterange(b.check_in, b.check_out, '[)');
```

### Resolución

1. **Si constraint falta**
   ```bash
   # Conectar a BD y ejecutar:
   ALTER TABLE reservations
   ADD CONSTRAINT no_overlap_reservations
   EXCLUDE USING gist (accommodation_id WITH =, period WITH &&)
   WHERE (reservation_status IN ('pre_reserved', 'confirmed'));
   ```

2. **Si datos conflictivos ya existen**
   - Identificar manualmente
   - Cancelar una de las reservas (cambiar estado a 'cancelled')
   - Notificar a clientes

3. **Root cause**
   - Check: ¿Alembic migration 001 corrió?
   - Check: ¿Migration tiene `btree_gist` extension?
   - Si no: manual fix + rollback (ver arriba)

---

## Checklist Rápido para TODO Incidente

1. [ ] **Assess:** ¿Crítico o Warning? ¿Cuántos users afectados?
2. [ ] **Gather:** Logs, métricas, estado de servicios
3. [ ] **Triage:** ¿Es código? ¿Infra? ¿Terceros?
4. [ ] **Act:** Restart < Rollback < Scale Up < DB fix
5. [ ] **Monitor:** Esperar 5–10 min para confirmar resolución
6. [ ] **Communicate:** Slack update, root cause doc
7. [ ] **Postmortem:** Si > 30 min outage, análisis al día siguiente

---

## Emergency Contacts

| Caso | Acción |
|------|--------|
| Desconocido / Caótico | Rollback inmediato |
| DB definitivamente roto | Restore from backup (ver disaster-recovery.md) |
| Attack / Abuse | Rate limit; IP ban; contact provider |

---

## Comandos Útiles (Copiar/Pegar)

```bash
# Status rápido
flyctl status -a sist-cabanas-prod

# Tail logs
flyctl logs -a sist-cabanas-prod -f

# Restart
flyctl restart -a sist-cabanas-prod

# Rollback
flyctl releases rollback -a sist-cabanas-prod

# SSH into instance (debug)
flyctl ssh console -a sist-cabanas-prod
  # Inside: tail /app/logs/app.log

# Scale
flyctl scale count 2 -a sist-cabanas-prod
flyctl scale vm shared-cpu-2x -a sist-cabanas-prod
```

---

**Última actualización:** 2025-10-26
**Responsable:** DevOps Lead
**Próxima revisión:** Post-MVP (mejora con métricas reales)
