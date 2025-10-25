# 🚀 Guía de Activación a Producción - SIST_CABAÑAS MVP

**Estado**: ✅ LISTO PARA ACTIVACIÓN
**Fecha**: Octubre 20, 2025
**Versión**: 1.0

---

## 📋 Tabla de Contenidos

1. [Estado Actual](#estado-actual)
2. [Prerequisitos](#prerequisitos)
3. [Opción A: Activación Automática (Recomendada)](#opción-a-activación-automática)
4. [Opción B: Activación Manual (Control Total)](#opción-b-activación-manual)
5. [Troubleshooting](#troubleshooting)
6. [Post-Deploy](#post-deploy)

---

## 🎯 Estado Actual

| Componente | Estado | Detalles |
|---|---|---|
| Backend MVP | ✅ Completo | 6,805 líneas, 180+ tests, 85%+ coverage |
| Fly.io CLI | ✅ Instalado | v0.3.195, PATH configurado |
| Autenticación Fly.io | ⏳ Pendiente | Requiere login interactivo (2-3 min) |
| Scripts Activación | ✅ Completos | 5 archivos, 920+ líneas totales |
| Validación Pre-Deploy | ✅ Lista | 15/15 checks disponibles |
| Git | ✅ Committed | Commit 44cc3a8, pushed a origin/main |

---

## ✅ Prerequisitos

Antes de empezar, verifica:

```bash
# 1. Terminal en directorio correcto
cd /home/eevan/ProyectosIA/SIST_CABAÑAS

# 2. Flyctl disponible
export PATH="/home/eevan/.fly/bin:$PATH"
flyctl version
# Debería mostrar: flyctl v0.3.195 linux/amd64

# 3. Git clean
git status
# Debería mostrar: nothing to commit, working tree clean
```

---

## 🚀 Opción A: Activación Automática (RECOMENDADA)

**Tiempo**: ~25 minutos
**Complejidad**: Baja
**Ventaja**: Todo automatizado, validaciones integradas

### Paso 1: FASE 0 - Autenticación (2-3 minutos)

```bash
# Configurar PATH
export PATH="/home/eevan/.fly/bin:$PATH"

# Login con Fly.io (se abre browser automáticamente)
flyctl auth login

# Autoriza en el browser
# → Click en "Authorize"
# → Vuelve al terminal

# Verifica autenticación
flyctl auth whoami
# ✅ Debería mostrar: tu_email@ejemplo.com
```

### Paso 2: Re-validación

```bash
# Ejecutar validación (debe mostrar 15/15 ✅)
./pre_deploy_validation.sh

# ✅ Output esperado:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REPORTE FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ Validación exitosa: 15/15 checks
```

### Paso 3: Iniciar Activación Automática

```bash
# Ejecutar script maestro
bash activation_complete.sh

# El script:
# 1. Confirmará inicio
# 2. Ejecutará FASE 1 (PostgreSQL + Secretos) ~10 min
# 3. Pausará para confirmar
# 4. Ejecutará FASE 2 (Deploy) ~5 min
# 5. Pausará para confirmar
# 6. Ejecutará FASE 3 (Smoke Tests) ~5 min
# 7. Mostrará resultado final

# Si todo OK, verás:
# ╔════════════════════════════════════════════╗
# ║ 🎉 ¡ACTIVACIÓN COMPLETADA EXITOSAMENTE! 🎉 ║
# ║ 🌐 URL: https://sist-cabanas-mvp.fly.dev  ║
# ╚════════════════════════════════════════════╝
```

### Paso 4: Verificar Producción

```bash
# Test endpoints
curl https://sist-cabanas-mvp.fly.dev/api/v1/healthz | jq .
curl https://sist-cabanas-mvp.fly.dev/api/v1/readyz | jq .

# Ver logs en vivo
flyctl logs -f --app sist-cabanas-mvp

# Ver dashboard
flyctl status --app sist-cabanas-mvp
```

---

## 🔧 Opción B: Activación Manual (CONTROL TOTAL)

**Tiempo**: ~25-30 minutos
**Complejidad**: Media
**Ventaja**: Control granular, debugging más fácil

### FASE 0: Autenticación (2-3 minutos)

```bash
export PATH="/home/eevan/.fly/bin:$PATH"
flyctl auth login
flyctl auth whoami  # Verifica ✅
./pre_deploy_validation.sh  # Debe mostrar 15/15 ✅
```

### FASE 1: Setup Fly.io (8-12 minutos)

```bash
bash fase_1_setup.sh

# El script:
# 1. Verifica prerequisitos
# 2. Crea PostgreSQL en región eze
# 3. Conecta DB a app
# 4. Genera 5 secretos
# 5. Configura secretos en Fly.io
# 6. Verifica configuración final

# ✅ Output esperado al final:
# REPORTE FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📋 Secretos configurados...
# 📊 Apps disponibles...
# ✅ FASE 1 COMPLETADA EXITOSAMENTE
```

### FASE 2: Deploy a Producción (3-5 minutos)

```bash
bash fase_2_deploy.sh

# El script:
# 1. Re-valida (15/15 checks)
# 2. Ejecuta: flyctl deploy --strategy immediate
# 3. Monitorea logs por 30 segundos
# 4. Muestra información de deploy

# ✅ Output esperado:
# ✅ VALIDACIÓN EXITOSA: 15/15 ✅
# ⏳ Iniciando deploy...
# ✅ DEPLOY COMPLETADO EXITOSAMENTE
# 🌐 URL de producción: https://sist-cabanas-mvp.fly.dev
```

### FASE 3: Smoke Tests (3-5 minutos)

```bash
bash fase_3_smoke_tests.sh

# El script ejecuta 5 tests:
# TEST 1: Health check (/api/v1/healthz)
# TEST 2: Readiness (/api/v1/readyz)
# TEST 3: Metrics (/metrics)
# TEST 4: Homepage (/)
# TEST 5: Database connectivity (SSH)

# ✅ Output esperado:
# ✅ Tests pasados:  5/5
# ❌ Tests fallidos: 0/5
# 🎉 ¡FASE 3 COMPLETADA EXITOSAMENTE! 🎉
# 🚀 APLICACIÓN EN PRODUCCIÓN
# https://sist-cabanas-mvp.fly.dev
```

---

## 🆘 Troubleshooting

### Error: "flyctl: command not found"

```bash
# Solución: Configurar PATH
export PATH="/home/eevan/.fly/bin:$PATH"

# Para persistencia, añade a ~/.bashrc:
echo 'export PATH="/home/eevan/.fly/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Error: "No access token available"

```bash
# Solución: Hacer login
flyctl auth login

# Verifica:
flyctl auth whoami
```

### Error: "FASE 1 falla en crear PostgreSQL"

```bash
# Verificar si app existe
flyctl apps list | grep sist-cabanas-mvp

# Si no existe, debes crearla primero
flyctl launch

# Si existe, prueba:
flyctl postgres create \
  --name sist-cabanas-db \
  --region eze \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1
```

### Error: "FASE 2 falla en deploy"

```bash
# Ver logs detallados
flyctl logs -f --app sist-cabanas-mvp

# Ver errores de compilación
flyctl builds list --app sist-cabanas-mvp

# Rollback a versión anterior
flyctl releases list --app sist-cabanas-mvp
flyctl releases rollback --app sist-cabanas-mvp
```

### Error: "Smoke tests fallan"

```bash
# SSH a la máquina para debugging
flyctl ssh console --app sist-cabanas-mvp

# Dentro del SSH:
# Ver logs de la app
journalctl -f

# Probar DB directamente
psql $DATABASE_URL -c "SELECT version();"

# Ver variables de entorno
env | grep -E "(DATABASE|REDIS|JWT)"
```

### Error: "Health check timeout"

```bash
# Puede estar en cold start, esperar 30s y reintentar
curl https://sist-cabanas-mvp.fly.dev/api/v1/healthz

# O ver logs para el error específico
flyctl logs -f --app sist-cabanas-mvp | grep -i error
```

---

## 📊 Post-Deploy

### Monitoreo Inicial (Primera Hora)

```bash
# Terminal 1: Logs en vivo
flyctl logs -f --app sist-cabanas-mvp

# Terminal 2: Monitoreo de status
watch -n 5 'flyctl status --app sist-cabanas-mvp'

# Terminal 3: Test health check cada 30s
watch -n 30 'curl -s https://sist-cabanas-mvp.fly.dev/api/v1/healthz | jq .'
```

### Comandos Útiles

```bash
# Ver status general
flyctl status --app sist-cabanas-mvp

# Ver configuración
flyctl config show --app sist-cabanas-mvp

# Ver secretos (ocultos)
flyctl secrets list --app sist-cabanas-mvp

# Ver releases (historial de deploys)
flyctl releases list --app sist-cabanas-mvp

# Rollback rápido
flyctl releases rollback --app sist-cabanas-mvp

# Escalar máquina (si es necesario)
flyctl scale vm shared-cpu-2x --app sist-cabanas-mvp

# SSH directa
flyctl ssh console --app sist-cabanas-mvp

# SCP archivos
flyctl ssh sftp shell --app sist-cabanas-mvp
```

### Monitoring Endpoints

| Endpoint | Propósito | Frecuencia |
|---|---|---|
| `GET /api/v1/healthz` | Health check general | Cada 30s |
| `GET /api/v1/readyz` | Readiness check | Cada 30s |
| `GET /metrics` | Prometheus metrics | Cada 1m |
| `POST /api/v1/admin/check` | Admin checks | Manual |

### Métricas Clave a Monitorear

```
• Error rate: <1% (alerta > 5%)
• Latencia P95: <3s para texto, <15s para audio
• Database latency: <100ms
• iCal sync age: <20 minutos
• Disponibilidad: >99.9%
```

---

## 🎯 Checklist Final

- [ ] FASE 0: Flyctl login exitoso
- [ ] FASE 0: Validación re-ejecutada (15/15 ✅)
- [ ] FASE 1: PostgreSQL creado en eze
- [ ] FASE 1: 5 secretos configurados
- [ ] FASE 2: Deploy sin errores
- [ ] FASE 3: 5/5 smoke tests PASADOS
- [ ] Aplicación accesible en https://sist-cabanas-mvp.fly.dev
- [ ] Logs sin errores críticos (primera hora)
- [ ] Health check respondiendo
- [ ] Métricas disponibles

---

## 📞 Soporte & Referencias

### Documentación
- Guía rápida: `QUICK_START.sh`
- Pre-deploy: `pre_deploy_validation.sh`
- Índice completo: `INDEX.md`
- Troubleshooting Fly.io: `docs/fly-io/FLY_IO_TROUBLESHOOTING.md`

### Scripts Disponibles
- `activation_complete.sh` - Maestro (todas las fases)
- `fase_1_setup.sh` - Setup Fly.io
- `fase_2_deploy.sh` - Deploy
- `fase_3_smoke_tests.sh` - Smoke tests

### URLs de Producción
- **App**: https://sist-cabanas-mvp.fly.dev
- **Dashboard**: https://fly.io/apps/sist-cabanas-mvp
- **API**: https://sist-cabanas-mvp.fly.dev/api/v1
- **Metrics**: https://sist-cabanas-mvp.fly.dev/metrics

---

**¡Listo para ir a producción! 🚀**

Tiempo total: ~25 minutos desde login hasta APP EN VIVO
