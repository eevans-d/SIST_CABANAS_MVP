# Disaster Recovery & Backup Procedures

> **Objetivo:** Restaurar servicio desde backup en caso de pérdida de datos o corrupción BD.
> **RTO (Recovery Time Objective):** < 15 min
> **RPO (Recovery Point Objective):** < 1 hora (backup diario + WAL)

---

## Parte 1: Backup Strategy (Preventivo)

### 1.1) Backups Automáticos (Fly Postgres)

Fly Postgres automáticamente:
- ✅ Backup completo: diario a las 00:00 UTC
- ✅ Retención: 7 días
- ✅ Ubicación: Fly infraestructura (ezeiza)

**Validación:**
```bash
# Ver backups disponibles
flyctl postgres backups list -a sist-cabanas-db
```

### 1.2) Backups Manuales (Antes de Cambios)

```bash
# Antes de despliegue importante, hacer backup manual
flyctl postgres backups create -a sist-cabanas-db --desc "Pre-deploy v1.2"

# Verificar
flyctl postgres backups list -a sist-cabanas-db
```

### 1.3) WAL (Write-Ahead Logging)

Fly Postgres guarda WAL automáticamente → permite restauración a punto en el tiempo.

---

## Parte 2: Restore Scenarios

### Escenario A: Corrupción de Datos (Tabla específica)

**Problema:** Datos en `reservations` corrupto; necesito restaurar esa tabla únicamente.

**Procedimiento:**

1. **Crear DB temporal desde backup**
   ```bash
   # Usa backup ID de lista anterior
   flyctl postgres backups restore 20251026-230000 \
     -a sist-cabanas-db \
     --restore-as sist-cabanas-temp
   ```

2. **Dump tabla específica desde temporal**
   ```bash
   # Conectar a DB temporal
   flyctl postgres connect sist-cabanas-temp

   # En psql:
   pg_dump -U postgres -d postgres -t reservations \
     -f reservations_backup.sql

   # Salir de psql
   \q
   ```

3. **Restaurar tabla en DB principal**
   ```bash
   # Conectar a DB principal
   flyctl postgres connect sist-cabanas-db

   # En psql:
   -- Truncar tabla (cuidado!)
   TRUNCATE TABLE reservations CASCADE;

   -- Restaurar
   \i reservations_backup.sql

   -- Validar
   SELECT COUNT(*) FROM reservations;

   \q
   ```

4. **Verificar app**
   ```bash
   curl https://tu-dominio.com/api/v1/healthz
   ```

5. **Eliminar DB temporal**
   ```bash
   flyctl postgres destroy sist-cabanas-temp
   ```

---

### Escenario B: BD Completamente Corrupta (Punto en el Tiempo)

**Problema:** BD completamente corrupta; restaurar a 3 horas atrás.

**Procedimiento:**

1. **Crear BD desde backup**
   ```bash
   # Usar backup del timestamp deseado
   flyctl postgres backups restore 20251026-180000 \
     -a sist-cabanas-db \
     --restore-as sist-cabanas-restored
   ```

2. **Validar integridad**
   ```bash
   flyctl postgres connect sist-cabanas-restored

   -- En psql:
   SELECT COUNT(*) FROM accommodations;
   SELECT COUNT(*) FROM reservations;
   SELECT * FROM reservations LIMIT 1;

   \q
   ```

3. **Swap: Mover DB restaurada a principal**
   ```bash
   # Opción A: Fly Postgres permite rename/attachment
   # (Depende de Fly CLI features; consultar docs)

   # Opción B: Dump & restore (más lento pero seguro)
   # Ver Escenario A arriba
   ```

4. **Restart backend**
   ```bash
   flyctl restart -a sist-cabanas-prod
   sleep 30
   curl https://tu-dominio.com/api/v1/healthz
   ```

5. **Limpieza**
   ```bash
   flyctl postgres destroy sist-cabanas-db
   # O rename a sist-cabanas-corrupted si quieres investigar
   ```

---

### Escenario C: Pérdida Total de BD (Plan Nuclear)

**Problema:** BD perdida/borrada accidentalmente; restaurar desde cero.

**Procedimiento:**

1. **Crear BD nueva desde backup más reciente**
   ```bash
   flyctl postgres backups restore latest \
     -a sist-cabanas-db \
     --restore-as sist-cabanas-db-restored
   ```

2. **Esperar 5–10 min por creación**
   ```bash
   watch 'flyctl postgres status -a sist-cabanas-db-restored'
   ```

3. **Adjuntar a app backend**
   ```bash
   # Actualizar DATABASE_URL en secrets
   NEW_DB_URL=$(flyctl postgres credentials show sist-cabanas-db-restored \
     | grep "Connection String" | cut -d: -f2- | xargs)

   flyctl secrets set DATABASE_URL="$NEW_DB_URL" -a sist-cabanas-prod
   ```

4. **Restart backend**
   ```bash
   flyctl restart -a sist-cabanas-prod
   sleep 30
   curl https://tu-dominio.com/api/v1/healthz
   ```

5. **Borra DB antigua si no la necesitas**
   ```bash
   flyctl postgres destroy sist-cabanas-db
   ```

---

### Escenario D: Desastre de Aplicación (Rollback)

**Problema:** Nuevo código broke todo; rollback necesario.

**Procedimiento:**

1. **Revert a versión anterior**
   ```bash
   flyctl releases -a sist-cabanas-prod | head -10  # Ver releases

   flyctl releases rollback -a sist-cabanas-prod
   ```

2. **Verificar**
   ```bash
   curl https://tu-dominio.com/api/v1/healthz
   ```

3. **Si rollback no es suficiente** (BD schema cambió):
   - Usar Alembic downgrade:
     ```bash
     alembic downgrade -1  # O específico: alembic downgrade 9a9b7f3c3e2f
     ```
   - Pero esto requiere SQL directo; mejor:
     - Mantener DB en versión anterior en secrets
     - O estar preparado con migration downgrades en el repo

---

## Parte 3: Testing Restore (Recomendado Mensual)

### Test Plan

```bash
# 1. Crear BD test desde backup (no toca producción)
flyctl postgres backups restore latest \
  -a sist-cabanas-db \
  --restore-as sist-cabanas-test

# 2. Validar datos intactos
flyctl postgres connect sist-cabanas-test
# En psql: SELECT COUNT(*) FROM accommodations, reservations, payments;

# 3. Destruir
flyctl postgres destroy sist-cabanas-test

# 4. Documentar: "✅ Restore test passed Oct 26"
```

---

## Parte 4: Monitoreo de Backups

### Alertas a Configurar

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Último backup > 26h | Alert | Trigger manual; verificar job |
| Backup size change | > 50% ↑ | Investigate; DB corruption? |
| Restore test fail | Cualquiera | Página a DevOps immediately |

### Script de Verificación (cron diario)

```bash
#!/bin/bash
# ops/backup_verify.sh

LATEST=$(flyctl postgres backups list -a sist-cabanas-db | head -2 | tail -1)
if [[ -z "$LATEST" ]]; then
  echo "ERROR: No backup found!" | mail -s "DB Backup Alert" devops@tu-dominio.com
  exit 1
fi

echo "✅ Latest backup: $LATEST"
```

Agregar a cron:
```
0 2 * * * cd /home/app && bash ops/backup_verify.sh
```

---

## Parte 5: Runbook de Desastre (Quick Ref)

### Si todo falla (3 minutos)

```bash
# STEP 1: STOPGAP (parar el sangrado)
flyctl restart -a sist-cabanas-prod  # Si es app issue
flyctl restart -a sist-cabanas-db    # Si es DB issue

# STEP 2: CHECK
flyctl logs -a sist-cabanas-prod | grep -i error | tail -20

# STEP 3: RESTORE (si no hay fix rápido)
flyctl postgres backups restore latest -a sist-cabanas-db --restore-as sist-cabanas-restored
# Esperar 10 min...
flyctl postgres connect sist-cabanas-restored
  # En psql: SELECT COUNT(*) FROM reservations;  # Validar
flyctl postgres destroy sist-cabanas-db
# Renombrar -restored → -db (o adjuntar a app)

# STEP 4: NOTIFY
# Slack: "🔴 Production incident. ETA 10 min fix. Restore in progress."
```

---

## Parte 6: Checklist Post-Disaster

- [ ] BD restaurada y validada
- [ ] App reiniciada y healthy
- [ ] Datos verificados (no datos parciales)
- [ ] Clientes notificados (si fue > 30 min)
- [ ] Postmortem planificado (próximas 24h)
- [ ] Causa root documentada
- [ ] Prevención implementada (si aplica)
- [ ] Backup de disaster state guardado (para análisis)

---

## Parte 7: Documentación de Cambios

Después de cualquier restore/disaster:

```markdown
## Incident Report - Oct 26, 14:00 UTC

**Timestamp:** 2025-10-26 14:00 UTC
**Duration:** 45 min
**Impact:** Reservations endpoint unavailable
**Root Cause:** DB constraint violated by webhook loop
**Resolution:** Rollback code + restore reservations table
**Action Items:**
- [ ] Webhook idempotency audit (PR #42)
- [ ] Backup test automation (PR #43)
- [ ] Alert threshold tuning (PR #44)
```

Guardar en `backend/docs/incidents/INCIDENT_20251026.md`.

---

## Contactos

| Rol | Disponibilidad | Acción |
|-----|---|---|
| DB Admin | 24/7 en-call | Restore / Migration |
| DevOps | 09:00-18:00 ART | Infrastructure |
| CTO | Alerta sólo | Decisión rollback/restore |

---

**Última actualización:** 2025-10-26
**Responsable:** DevOps Lead
**Testing Schedule:** Primer viernes de cada mes
