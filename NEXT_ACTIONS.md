# 🚀 NEXT ACTIONS - Fases de Activación Post-Validación

**Fecha:** 2025-10-19  
**Estado Actual:** ✅ Validación pre-deployment completada (13/15)  
**Bloqueante:** Flyctl CLI (5 min)  
**Próxima Fase:** Deploy a Fly.io (15 min total)

---

## 📋 FASES DE ACTIVACIÓN

### ⏱️ FASE 0: AHORA (5 minutos) - Resolver Bloqueante

```bash
# 1. Instalar Fly.io CLI
curl -L https://fly.io/install.sh | sh

# 2. Configurar PATH
echo 'export PATH="/home/eevan/.fly/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 3. Verificar instalación
flyctl version
flyctl auth whoami  # Debe estar autenticado

# 4. Re-validar sistema
cd /home/eevan/ProyectosIA/SIST_CABAÑAS
./pre_deploy_validation.sh
# Resultado esperado: ✅ 15/15 checks PASADOS (100%)
```

**Success Criteria:**
```
✅ 15/15 checks PASADOS
✅ Bloqueante resuélto
⏱️ Tiempo: 5 min
→ Proceder a FASE 1
```

---

### ⏱️ FASE 1: Setup de Fly.io (10 minutos)

#### Paso 1A: Crear PostgreSQL (1 min)

```bash
flyctl postgres create \
  --name sist-cabanas-db \
  --region eze \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1

# Respuesta esperada:
# "Your postgres cluster 'sist-cabanas-db' is ready!"
```

#### Paso 1B: Conectar DB a la App (1 min)

```bash
flyctl postgres attach sist-cabanas-db --app sist-cabanas-mvp

# Verifica que DATABASE_URL se añadió como secreto
flyctl secrets list --app sist-cabanas-mvp | grep DATABASE_URL
```

#### Paso 1C: Generar Secretos Seguros (2 min)

```bash
# Generar valores aleatorios
JWT_SECRET=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
ICS_SALT=$(openssl rand -base64 16)
ADMIN_CSRF_SECRET=$(openssl rand -base64 32)
GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 12)

# Guardar en archivo temporal (solo para esta sesión)
cat > /tmp/secrets.env << EOF
JWT_SECRET=$JWT_SECRET
REDIS_PASSWORD=$REDIS_PASSWORD
ICS_SALT=$ICS_SALT
ADMIN_CSRF_SECRET=$ADMIN_CSRF_SECRET
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD
EOF

echo "✅ Secretos generados. Archivo temporal: /tmp/secrets.env"
```

#### Paso 1D: Configurar Secretos en Fly.io (6 min)

**CRÍTICOS (valores generados arriba):**
```bash
flyctl secrets set \
  JWT_SECRET="$JWT_SECRET" \
  REDIS_PASSWORD="$REDIS_PASSWORD" \
  ICS_SALT="$ICS_SALT" \
  ADMIN_CSRF_SECRET="$ADMIN_CSRF_SECRET" \
  GRAFANA_ADMIN_PASSWORD="$GRAFANA_ADMIN_PASSWORD" \
  --app sist-cabanas-mvp
```

**APIs EXTERNAS (requieren valores reales - ESPERAR CREDENCIALES):**
```bash
# ⚠️ REQUIERE: Meta Business Suite (WhatsApp)
flyctl secrets set \
  WHATSAPP_VERIFY_TOKEN="<generate_or_obtain_from_meta>" \
  WHATSAPP_APP_SECRET="<from_meta_app_dashboard>" \
  WHATSAPP_TOKEN="<from_meta_access_token>" \
  WHATSAPP_PHONE_ID="<from_whatsapp_business>" \
  --app sist-cabanas-mvp

# ⚠️ REQUIERE: Mercado Pago Credentials
flyctl secrets set \
  MERCADOPAGO_ACCESS_TOKEN="<from_mercadopago_credentials>" \
  MERCADOPAGO_PUBLIC_KEY="<from_mercadopago_credentials>" \
  --app sist-cabanas-mvp

# ⚠️ REQUIERE: Email App Password (Gmail, Outlook, etc)
flyctl secrets set \
  SMTP_PASS="<email_app_password>" \
  --app sist-cabanas-mvp

# ⚠️ REQUIERE: Para Irnos API Token (opcional)
# flyctl secrets set \
#   PARA_IRNOS_API_TOKEN="<from_para_irnos>" \
#   --app sist-cabanas-mvp
```

**VERIFICAR SECRETOS CONFIGURADOS:**
```bash
flyctl secrets list --app sist-cabanas-mvp

# Esperado: Lista de 8+ secretos
# Críticos: DATABASE_URL, JWT_SECRET, REDIS_PASSWORD, ICS_SALT, ADMIN_CSRF_SECRET, GRAFANA_ADMIN_PASSWORD
# Externos: WHATSAPP_*, MERCADOPAGO_*, SMTP_PASS
```

**Success Criteria:**
```
✅ PostgreSQL creado (región eze)
✅ DB conectada a app
✅ 5 secretos críticos configurados
✅ (3 secretos de APIs externos - según disponibilidad)
⏱️ Tiempo: 10 min
→ Proceder a FASE 2
```

---

### ⏱️ FASE 2: Deploy Inicial (5 minutos)

#### Paso 2A: Verificar Configuración (1 min)

```bash
cd /home/eevan/ProyectosIA/SIST_CABAÑAS

# Validar configuración de nuevo
./pre_deploy_validation.sh

# Debe ser: ✅ 15/15 checks PASADOS
```

#### Paso 2B: Deploy a Fly.io (4 min)

```bash
# Deploy inicial (primera vez tarda ~4 min)
flyctl deploy --app sist-cabanas-mvp --strategy immediate

# Monitorear en otra terminal (NO CIERRE ESTA):
flyctl logs -f --app sist-cabanas-mvp
```

**Qué esperar en logs:**
```
[Logs] Using Buildpacks to build the image
[Logs] Running: docker build...
[Logs] Image successfully built
[Logs] Releasing new machine version 1
[Logs] Release command: alembic upgrade head
[Logs] Migrations completed successfully
[Logs] Starting application on port 8080
[Logs] Application started successfully
```

**Si falla:**
```bash
# Ver error completo
flyctl logs --app sist-cabanas-mvp | tail -50

# Rollback si es necesario
flyctl releases list --app sist-cabanas-mvp
flyctl releases rollback --app sist-cabanas-mvp
```

**Success Criteria:**
```
✅ Build successful
✅ Release command passed (migrations OK)
✅ Health check passing
✅ Application listening on 0.0.0.0:8080
⏱️ Tiempo: 5 min
→ Proceder a FASE 3
```

---

### ⏱️ FASE 3: Smoke Tests (5 minutos)

#### Test 1: Health Check

```bash
# Health endpoint
curl -s https://sist-cabanas-mvp.fly.dev/api/v1/healthz | jq .

# Esperado:
# {
#   "status": "healthy",
#   "checks": {
#     "database": {"status": "ok", "latency_ms": 15},
#     "ical_sync": {"status": "ok", "last_sync_minutes_ago": 2}
#   }
# }
```

#### Test 2: Readiness

```bash
curl -s https://sist-cabanas-mvp.fly.dev/api/v1/readyz | jq .

# Esperado:
# {
#   "status": "ready"
# }
```

#### Test 3: Metrics

```bash
curl -s https://sist-cabanas-mvp.fly.dev/metrics | head -20

# Esperado:
# # HELP http_requests_total Total HTTP requests
# # TYPE http_requests_total counter
# http_requests_total{endpoint="/api/v1/healthz",method="GET",status="200"} 1.0
```

#### Test 4: Homepage

```bash
curl -I https://sist-cabanas-mvp.fly.dev/

# Esperado:
# HTTP/2 200 
# content-type: text/html; charset=utf-8
```

#### Test 5: Database Connection

```bash
# SSH a container y verificar DB
flyctl ssh console --app sist-cabanas-mvp

# Dentro del container:
psql $DATABASE_URL -c "SELECT version();"
# Esperado: PostgreSQL 16...

# Verificar migraciones
psql $DATABASE_URL -c "SELECT version FROM alembic_version;"
# Esperado: Lista de versiones de migración

# Salir
exit
```

**Success Criteria:**
```
✅ Health: 200 OK, status=healthy
✅ Readiness: 200 OK, status=ready
✅ Metrics: 200 OK, datos de Prometheus
✅ Homepage: 200 OK
✅ Database: Conectada, migraciones OK
⏱️ Tiempo: 5 min
→ DEPLOYMENT EXITOSO
```

---

## 🎯 RESUMEN DE TIMELINE

```
INICIO: Instalar flyctl (5 min)
│
├─ FASE 1: Setup Fly.io (10 min)
│  ├─ Crear PostgreSQL
│  ├─ Conectar DB
│  ├─ Generar secretos
│  └─ Configurar en Fly.io
│
├─ FASE 2: Deploy (5 min)
│  ├─ Verificar validación
│  ├─ flyctl deploy
│  └─ Monitorear logs
│
└─ FASE 3: Smoke Tests (5 min)
   ├─ Health check
   ├─ Readiness
   ├─ Metrics
   ├─ Homepage
   └─ Database
   
TOTAL: ~25 minutos
RESULTADO: ✅ PRODUCTION LIVE
```

---

## ⚠️ DECISIONES IMPORTANTES

### Secretos Externos (APIs)

**DECISIÓN:** Configurar secretos críticos primero, APIs externas después.

**Razón:** El sistema puede funcionar sin APIs (con fallos graceful):
- WhatsApp webhook no funcionará (pero app sigue viva)
- Mercado Pago webhook no funcionará (pero app sigue viva)
- Email no se enviará (pero app sigue viva)

**Implicación:** Deploy sin APIs = Sistema funcional pero sin integraciones.

**Recomendación:**
```
1. Deploy con secretos críticos AHORA (15 min)
2. Validar sistema vive sin APIs
3. Añadir APIs después (no requiere re-deploy)
   flyctl secrets set WHATSAPP_VERIFY_TOKEN="..." --app sist-cabanas-mvp
   flyctl secrets set MERCADOPAGO_ACCESS_TOKEN="..." --app sist-cabanas-mvp
```

---

## 🔄 POST-DEPLOYMENT (Semana 1)

### Día 1: Monitoring
```bash
# Logs continuos
flyctl logs -f --app sist-cabanas-mvp

# Métricas
curl https://sist-cabanas-mvp.fly.dev/metrics | grep http_requests_total

# Error rate
curl https://sist-cabanas-mvp.fly.dev/metrics | grep http_requests_total.*500
```

### Día 2-3: Webhook Testing
```bash
# Test WhatsApp webhook
# (si credenciales configuradas)

# Test Mercado Pago webhook
# (si credenciales configuradas)

# Test iCal sync
# Ver en logs: "ical_sync_completed"
```

### Día 4-7: Performance Monitoring
```bash
# P95 response time
curl https://sist-cabanas-mvp.fly.dev/metrics | grep http_request_duration_seconds

# Error rate
error_rate = (http_requests_total{status=~"5.."} / http_requests_total) * 100
# Target: < 1%

# iCal sync age
curl https://sist-cabanas-mvp.fly.dev/metrics | grep ical_last_sync_age_minutes
# Target: < 20 minutes
```

---

## 📋 CHECKLIST FINAL

### Pre-Deployment
- [ ] flyctl CLI instalado y autenticado
- [ ] ./pre_deploy_validation.sh → 15/15 ✅
- [ ] Git working tree clean
- [ ] Todos los commits pusheados

### Deployment
- [ ] PostgreSQL creado (región eze)
- [ ] Database conectada a app
- [ ] 5 secretos críticos configurados
- [ ] flyctl deploy ejecutado
- [ ] Build successful en logs
- [ ] Migraciones completadas en logs
- [ ] App listening on port 8080 en logs

### Post-Deployment
- [ ] Health check: 200 OK
- [ ] Readiness check: 200 OK
- [ ] Metrics disponibles: 200 OK
- [ ] Homepage responde: 200 OK
- [ ] Database conectada y migraciones OK
- [ ] 0 errores en logs (primeros 10 min)

### Monitoring (Semana 1)
- [ ] Error rate < 1%
- [ ] P95 response < 3s (texto)
- [ ] P95 response < 15s (audio)
- [ ] iCal sync < 20 min desfase
- [ ] Logs sin errores no esperados

---

## 🚨 TROUBLESHOOTING RÁPIDO

### Si flyctl build falla:
```bash
# Ver logs completos
flyctl logs --app sist-cabanas-mvp | grep -i error

# Opciones:
# 1. Memory issue: aumentar instancia
#    flyctl scale memory 512 --app sist-cabanas-mvp
# 2. Timeout: re-intentar deploy
#    flyctl deploy --app sist-cabanas-mvp --strategy immediate
# 3. Dockerfile issue: ejecutar localmente
#    cd backend && docker build --no-cache .
```

### Si release command falla:
```bash
# Verificar DATABASE_URL está configurado
flyctl secrets list --app sist-cabanas-mvp | grep DATABASE_URL

# Verificar migraciones son válidas
cd backend
alembic current  # Ver versión actual

# Re-desplegar sin release command
flyctl deploy --app sist-cabanas-mvp --skip-release
```

### Si health check timeout:
```bash
# SSH y verificar app escucha en 8080
flyctl ssh console --app sist-cabanas-mvp
lsof -i :8080
curl http://localhost:8080/api/v1/healthz

# Si no responde: app crasheó
exit
flyctl logs --app sist-cabanas-mvp | tail -50
```

---

## 📞 RECURSOS

- **Documentación:** INDEX.md
- **Validación:** ./pre_deploy_validation.sh
- **Guía:** DEPLOY_READY_CHECKLIST.md
- **Troubleshooting:** docs/fly-io/FLY_IO_TROUBLESHOOTING.md
- **Arquitectura:** docs/fly-io/FLY_IO_ARCHITECTURE.md

---

## 🎯 SIGUIENTE ACCIÓN INMEDIATA

```bash
# AHORA - Resolver bloqueante (5 min)
curl -L https://fly.io/install.sh | sh
export PATH="/home/eevan/.fly/bin:$PATH"
source ~/.bashrc
flyctl auth login

# LUEGO - Re-validar
cd /home/eevan/ProyectosIA/SIST_CABAÑAS
./pre_deploy_validation.sh
# Debe mostrar: ✅ 15/15 checks PASADOS

# DESPUÉS - Deploy (20 min)
# Ver FASE 1 + FASE 2 + FASE 3 arriba
```

---

**Estado:** 🟡 BLOQUEADO en Flyctl CLI (5 min)  
**Después:** 🟢 READY FOR DEPLOYMENT (20 min)  
**Final:** 🎉 PRODUCTION LIVE (25 min total)

---

*Documento generado como guía paso-a-paso para fases posteriores a validación*  
*Última ejecución del script: ./pre_deploy_validation.sh (13/15 PASADOS)*
