# 🔄 Plan de Rollback - Sistema MVP Alojamientos

**Versión:** v1.0
**Fecha:** 4 de Octubre, 2025
**Propósito:** Procedimientos de rollback para recuperación rápida ante fallos en deploy

---

## 📋 Índice

1. [Estrategia de Rollback](#estrategia-de-rollback)
2. [Procedimientos por Severidad](#procedimientos-por-severidad)
3. [Rollback Completo](#rollback-completo)
4. [Rollback Parcial](#rollback-parcial)
5. [Recuperación de Datos](#recuperación-de-datos)
6. [Checklist Post-Rollback](#checklist-post-rollback)

---

## 🎯 Estrategia de Rollback

### Principios

1. **Prioridad #1:** Restaurar servicio funcional lo más rápido posible
2. **Prioridad #2:** Preservar integridad de datos
3. **Prioridad #3:** Mantener comunicación con stakeholders

### Niveles de Severidad

| Nivel | Descripción | Tiempo de Respuesta | Acción |
|-------|-------------|-------------------|--------|
| 🔴 **SEV1 - Crítico** | Sistema completamente caído | < 5 minutos | Rollback completo inmediato |
| 🟠 **SEV2 - Mayor** | Funcionalidad crítica rota | < 15 minutos | Rollback parcial o completo |
| 🟡 **SEV3 - Menor** | Bug no crítico | < 1 hora | Fix forward o rollback parcial |
| 🟢 **SEV4 - Cosmético** | UI/UX issue | < 24 horas | Fix forward en próximo deploy |

### Puntos de No Retorno

**⚠️ ATENCIÓN:** Después de estos eventos, rollback completo NO es seguro:

1. ✅ **Migraciones irreversibles ejecutadas** (ej: DROP column)
2. ✅ **Datos de producción modificados** (sin backup reciente)
3. ✅ **Integraciones externas notificadas** (webhooks enviados a WhatsApp/MP)

---

## 🚨 Procedimientos por Severidad

### SEV1 - Crítico (Sistema Caído)

**Síntomas:**
- Health check retorna unhealthy o timeout
- 500 errors en todos los endpoints
- Base de datos inaccesible
- Contenedores crasheando en loop

**Procedimiento:**

```bash
# 1. STOP: Detener deploy inmediatamente
cd /opt/apps/SIST_CABANAS_MVP

# 2. Verificar estado actual
docker compose ps
docker compose logs --tail 50 api

# 3. Rollback a versión anterior (tag git)
git fetch --tags
git tag -l | tail -5  # Ver últimos tags

# Rollback al último tag estable (ej: v0.9.9)
git checkout v0.9.9

# 4. Rebuild y restart
docker compose down
docker compose up -d --build

# 5. Verificar health
curl https://staging.alojamientos.com/api/v1/healthz

# 6. Si falla, rollback de DB (solo si necesario)
# Ver sección "Recuperación de Datos"
```

**Tiempo estimado:** 5-10 minutos

---

### SEV2 - Mayor (Funcionalidad Crítica Rota)

**Síntomas:**
- Pre-reservas no se crean
- Webhooks no procesan eventos
- Pagos no confirman
- Email no envía

**Procedimiento:**

#### Opción A: Rollback Parcial de Código

```bash
cd /opt/apps/SIST_CABANAS_MVP

# 1. Identificar commit problemático
git log --oneline -10

# 2. Revertir commit específico (mantiene historial)
git revert <commit_hash> --no-edit

# 3. Rebuild solo el servicio afectado
docker compose up -d --build api

# 4. Verificar logs
docker compose logs -f api | grep ERROR
```

#### Opción B: Rollback Completo si Opción A falla

```bash
# Seguir procedimiento SEV1
git checkout <tag_estable_anterior>
docker compose down && docker compose up -d --build
```

**Tiempo estimado:** 10-20 minutos

---

### SEV3 - Menor (Bug No Crítico)

**Síntomas:**
- Rate limiting demasiado agresivo
- Logs con warnings no críticos
- Métricas no exportándose
- NLU con baja precisión

**Procedimiento:**

```bash
# PREFERIR FIX FORWARD sobre rollback

# 1. Analizar root cause
docker compose logs api | grep -i "error\|warn" | tail -100

# 2. Aplicar fix rápido (hotfix)
git checkout -b hotfix/sev3-fix
# ... hacer cambios ...
git commit -m "hotfix: fix SEV3 issue"
git push origin hotfix/sev3-fix

# 3. Deploy del hotfix
git checkout main
git merge hotfix/sev3-fix
docker compose up -d --build api

# 4. Verificar
bash scripts/post-deploy-verify.sh staging.alojamientos.com
```

**Tiempo estimado:** 30-60 minutos

---

## 🔄 Rollback Completo

### Pre-requisitos

- [ ] Backup de DB reciente (< 1 hora)
- [ ] Tag git del último deploy estable
- [ ] Acceso SSH al servidor
- [ ] Variables de entorno guardadas

### Procedimiento Paso a Paso

#### 1. Detener servicios actuales

```bash
cd /opt/apps/SIST_CABANAS_MVP

# Detener contenedores
docker compose down

# Verificar que todos están detenidos
docker compose ps
```

#### 2. Backup de estado actual (por si necesitas datos recientes)

```bash
# Backup de DB actual
docker compose up -d postgres
docker exec alojamientos_postgres pg_dump \
    -U alojamientos \
    -d alojamientos \
    -F c \
    -f /tmp/backup_before_rollback_$(date +%Y%m%d_%H%M%S).dump

# Copiar backup a host
docker cp alojamientos_postgres:/tmp/backup_before_rollback_*.dump \
    /var/backups/alojamientos/

# Detener postgres
docker compose down
```

#### 3. Rollback de código

```bash
# Verificar branch actual
git branch

# Ver últimos tags
git tag -l | tail -10

# Checkout al tag estable anterior
git fetch --tags
git checkout v0.9.9  # O el tag estable que necesites

# Verificar que estás en el tag correcto
git describe --tags
```

#### 4. Restaurar variables de entorno (si cambiaron)

```bash
# Verificar diferencias en .env.template
git diff HEAD v0.9.9 -- .env.template

# Si hay cambios críticos, actualizar .env manualmente
nano .env
```

#### 5. Rollback de migraciones de DB (si necesario)

```bash
# Levantar solo postgres
docker compose up -d postgres

# Esperar a que postgres esté ready
sleep 10

# Ver historial de migraciones
docker compose run --rm api alembic history

# Hacer downgrade a revisión anterior
# CUIDADO: Solo si sabes que es seguro
docker compose run --rm api alembic downgrade -1

# O downgrade a revisión específica
# docker compose run --rm api alembic downgrade <revision>
```

**⚠️ ADVERTENCIA:** Downgrade de migraciones puede causar pérdida de datos. Solo ejecutar si:
- Sabes exactamente qué hace el downgrade
- Tienes backup reciente
- Las migraciones son reversibles

#### 6. Rebuild y restart de servicios

```bash
# Levantar todos los servicios
docker compose up -d --build

# Verificar que todos están corriendo
docker compose ps

# Debe mostrar todos los contenedores en "Up" state
```

#### 7. Verificación post-rollback

```bash
# Ejecutar script de verificación
bash scripts/post-deploy-verify.sh staging.alojamientos.com

# O manualmente:
curl https://staging.alojamientos.com/api/v1/healthz
```

#### 8. Verificar logs por errores

```bash
# Ver logs de todos los servicios
docker compose logs --tail 100

# Filtrar por errores
docker compose logs | grep -i "error\|exception\|critical"

# Si no hay errores críticos → Rollback exitoso
```

---

## 🔧 Rollback Parcial

### Rollback solo de API (sin tocar DB/Redis)

```bash
cd /opt/apps/SIST_CABANAS_MVP

# Detener solo API
docker compose stop api

# Checkout a versión anterior
git checkout v0.9.9

# Rebuild y restart solo API
docker compose up -d --build api

# Verificar
docker compose ps
docker compose logs -f api
```

### Rollback solo de configuración (Nginx/env vars)

```bash
# Restaurar .env anterior (desde backup)
cp /var/backups/alojamientos/.env.backup .env

# Reiniciar servicios afectados
docker compose restart api

# O para nginx:
docker compose restart nginx
```

---

## 💾 Recuperación de Datos

### Restaurar Backup de PostgreSQL

#### Listar backups disponibles

```bash
ls -lah /var/backups/alojamientos/
```

#### Restaurar desde backup

```bash
# 1. Detener API para evitar conexiones activas
docker compose stop api

# 2. Copiar backup al contenedor
docker cp /var/backups/alojamientos/backup_20251004.dump \
    alojamientos_postgres:/tmp/

# 3. Drop y recrear DB (DESTRUCTIVO!)
docker exec alojamientos_postgres psql -U alojamientos -c \
    "DROP DATABASE IF EXISTS alojamientos;"

docker exec alojamientos_postgres psql -U alojamientos -c \
    "CREATE DATABASE alojamientos OWNER alojamientos;"

# 4. Restaurar backup
docker exec alojamientos_postgres pg_restore \
    -U alojamientos \
    -d alojamientos \
    -v \
    /tmp/backup_20251004.dump

# 5. Verificar datos restaurados
docker exec alojamientos_postgres psql -U alojamientos -d alojamientos -c \
    "SELECT COUNT(*) FROM reservations;"

# 6. Reiniciar API
docker compose up -d api
```

### Restaurar datos de Redis (si hay backup)

```bash
# Redis guarda dump.rdb automáticamente

# 1. Detener Redis
docker compose stop redis

# 2. Copiar backup anterior (si existe)
docker cp /var/backups/alojamientos/redis_dump.rdb \
    alojamientos_redis:/data/dump.rdb

# 3. Reiniciar Redis
docker compose up -d redis

# 4. Verificar keys
docker exec alojamientos_redis redis-cli --pass $REDIS_PASSWORD DBSIZE
```

---

## ✅ Checklist Post-Rollback

Después de ejecutar rollback, verificar:

### Infraestructura
- [ ] Todos los contenedores están en estado "Up"
- [ ] Health check retorna "healthy"
- [ ] No hay crashloop en logs recientes (últimos 5 min)

### Base de Datos
- [ ] Conexión a DB funcional
- [ ] Migraciones en revisión correcta (`alembic current`)
- [ ] Tablas críticas tienen datos:
  ```bash
  docker exec alojamientos_postgres psql -U alojamientos -d alojamientos -c \
      "SELECT COUNT(*) FROM accommodations; SELECT COUNT(*) FROM reservations;"
  ```

### API
- [ ] `/api/v1/healthz` responde "healthy"
- [ ] Endpoint de pre-reserva responde (aunque sea con 404/422)
- [ ] Webhooks responden a verificación

### Seguridad
- [ ] SSL certificate válido (si aplica)
- [ ] Security headers presentes
- [ ] Puertos DB/Redis NO expuestos públicamente

### Observabilidad
- [ ] Métricas `/metrics` accesibles
- [ ] Logs generándose sin errores críticos
- [ ] Timestamps de logs son actuales

### Funcional
- [ ] Pre-reserva de prueba se crea correctamente
- [ ] Health check de integraciones OK (WhatsApp, MP, Email)

---

## 📊 Comunicación Durante Rollback

### Template de Notificación

**Para stakeholders:**

```
🔄 ROLLBACK EN PROGRESO - Sistema MVP Alojamientos

Status: En proceso de rollback a versión estable anterior
Razón: [Descripción breve del problema]
Severidad: [SEV1/SEV2/SEV3]
Tiempo estimado de recuperación: [X minutos]

Acciones tomadas:
- [X] Rollback de código a v0.9.9
- [ ] Verificación de servicios
- [ ] Tests de funcionalidad

Estado actual:
- API: [Status]
- Base de datos: [Status]
- Integraciones: [Status]

Próxima actualización en: [X minutos]
```

**Para equipo técnico:**

```
🚨 ROLLBACK SEV[1/2/3]

Problem: [Descripción técnica]
Root cause: [Si se conoce]
Rollback strategy: [Completo/Parcial/Fix-forward]

Commands executed:
git checkout v0.9.9
docker compose down && docker compose up -d --build

Current status:
✓ Code rolled back
✓ Services restarted
⏳ Verification in progress

Logs:
[Adjuntar logs relevantes]
```

---

## 🎯 Prevención de Rollbacks Futuros

### Pre-Deploy Checklist (para reducir necesidad de rollback)

- [ ] Tests locales pasando: `make test`
- [ ] Pre-commit hooks pasando
- [ ] Coverage > 80%
- [ ] Smoke tests en staging pasando
- [ ] Security audit ejecutado
- [ ] Backup de DB reciente (< 1 hora)
- [ ] Tag git creado con versión
- [ ] Variables de entorno respaldadas
- [ ] Plan de rollback revisado y entendido

### Estrategia de Deploy Seguro

1. **Blue-Green Deploy** (Futuro):
   - Mantener versión anterior corriendo
   - Deploy nueva versión en paralelo
   - Switch de tráfico solo cuando nueva versión verificada

2. **Canary Deploy** (Futuro):
   - Deploy gradual (10% → 50% → 100% tráfico)
   - Monitorear métricas en cada fase

3. **Feature Flags**:
   - Activar features nuevas gradualmente
   - Rollback sin redeploy

---

## 📞 Contactos de Emergencia

| Rol | Contacto | Disponibilidad |
|-----|----------|----------------|
| DevOps Lead | [Tu contacto] | 24/7 |
| Backend Lead | [Tu contacto] | 9am-11pm |
| Infra Provider | [Proveedor] | Support ticket |

---

## 🔗 Referencias

- [Post-Deploy Verification Script](../scripts/post-deploy-verify.sh)
- [Pre-Deploy Check Script](../scripts/pre-deploy-check.sh)
- [Production Setup Guide](../../PRODUCTION_SETUP.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

**Última actualización:** 4 de Octubre, 2025
**Próxima revisión:** Después del primer deploy a producción
