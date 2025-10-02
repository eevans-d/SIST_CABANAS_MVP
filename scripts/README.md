# 🛠️ Scripts de Deploy y Mantenimiento

Este directorio contiene scripts automatizados para deployment, validación y testing del sistema.

## 📋 Scripts Disponibles

### 1. `pre-deploy-check.sh` ✅

**Propósito:** Validación completa pre-deploy  
**Uso:** `./scripts/pre-deploy-check.sh`  
**Duración:** ~30 segundos

**Verifica:**
- Archivo `.env` existe y tiene todas las variables críticas
- Variables no tienen valores por defecto inseguros
- `docker-compose.yml` sintácticamente correcto
- Puertos DB/Redis comentados (seguridad)
- `nginx.conf` generado con dominio real
- Tests unitarios pasan
- Estado de Git (limpio y en main)
- Requisitos del sistema (Docker, Docker Compose)
- Certificados SSL (si existen)

**Exit codes:**
- `0`: Todo OK, listo para deploy
- `1`: Errores críticos encontrados

**Ejemplo de salida:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔍 PRE-DEPLOY VALIDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[✓] .env existe
[✓] Variable DOMAIN configurada
[✓] docker-compose.yml sintácticamente correcto
[✓] Puerto PostgreSQL comentado (seguro)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 RESUMEN DE VALIDACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ TODO PERFECTO - Listo para deploy
```

---

### 2. `smoke-test-prod.sh` 🧪

**Propósito:** Tests básicos contra producción  
**Uso:** `BASE_URL=https://tu-dominio.com ./scripts/smoke-test-prod.sh`  
**Duración:** ~10 segundos

**Tests ejecutados:**
- Health endpoint responde
- Status es "healthy"
- Métricas accesibles
- OpenAPI schema disponible
- HTTP redirect a HTTPS (si aplica)
- Security headers presentes
- CORS configurado
- Tiempo de respuesta < 2s

**Variables de entorno:**
- `BASE_URL`: URL del sistema a testear (default: `https://localhost`)
- `TIMEOUT`: Timeout para requests (default: 10s)

**Ejemplo:**
```bash
# Testear producción
BASE_URL=https://alojamientos.tuempresa.com ./scripts/smoke-test-prod.sh

# Testear localhost
BASE_URL=http://localhost:8000 ./scripts/smoke-test-prod.sh
```

---

### 3. `deploy.sh` 🚀

**Propósito:** Deploy automatizado end-to-end  
**Uso:** `./scripts/deploy.sh`  
**Duración:** ~5-10 minutos

**Fases del deploy:**
1. **Validación:** Ejecuta `pre-deploy-check.sh`
2. **Config Nginx:** Genera `nginx.conf` desde template
3. **Backup:** Backup automático de DB si existe deployment previo
4. **Build:** Construye containers Docker
5. **Deploy:** Levanta todos los servicios
6. **Migraciones:** Ejecuta migraciones Alembic
7. **Smoke Tests:** Verifica que todo funciona

**Rollback automático:** Si el deploy falla, los backups están en `backups/YYYYMMDD_HHMMSS/`

**Ejemplo de salida:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🚀 SISTEMA ALOJAMIENTOS - DEPLOY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[INFO] Paso 1/6: Ejecutando validaciones pre-deploy...
[✓] Validaciones OK

[INFO] Paso 2/6: Generando configuración de Nginx...
[✓] nginx.conf generado

[INFO] Paso 3/6: Creando backup...
[✓] Backup creado en backups/20251002_143022

[INFO] Paso 4/6: Construyendo y desplegando containers...
[✓] Containers desplegados

[INFO] Paso 5/6: Ejecutando migraciones de base de datos...
[✓] Migraciones completadas

[INFO] Paso 6/6: Ejecutando smoke tests...
[✓] Smoke tests pasaron

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ DEPLOY COMPLETADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔄 Flujo de Trabajo Recomendado

### Primera vez (Producción nueva)

```bash
# 1. Clonar repo y configurar
git clone <repo-url>
cd SIST_CABANAS_MVP
cp .env.template .env
nano .env  # Completar variables productivas

# 2. Validar configuración
./scripts/pre-deploy-check.sh

# 3. Generar nginx.conf
cd backend && ./generate_nginx_conf.sh ../.env && cd ..

# 4. Deploy completo
./scripts/deploy.sh

# 5. Configurar webhooks
# - WhatsApp: https://TU-DOMINIO/api/v1/webhooks/whatsapp
# - Mercado Pago: https://TU-DOMINIO/api/v1/webhooks/mercadopago
```

### Deploy de actualización

```bash
# 1. Pull de cambios
git pull origin main

# 2. Validar
./scripts/pre-deploy-check.sh

# 3. Deploy (incluye backup automático)
./scripts/deploy.sh
```

### Verificación post-deploy

```bash
# Smoke tests
BASE_URL=https://tu-dominio.com ./scripts/smoke-test-prod.sh

# Health check manual
curl https://tu-dominio.com/api/v1/healthz | jq

# Ver logs
docker-compose -f backend/docker-compose.yml logs -f api

# Ver métricas
curl https://tu-dominio.com/metrics
```

---

## 🆘 Rollback

Si algo falla después del deploy:

```bash
# 1. Identificar último backup
ls -la backups/

# 2. Restaurar DB
docker-compose -f backend/docker-compose.yml exec -T db \
  psql -U alojamientos -d alojamientos_db < backups/YYYYMMDD_HHMMSS/db_backup.sql

# 3. Volver a versión anterior del código
git checkout <commit-anterior>
docker-compose -f backend/docker-compose.yml up -d --build

# 4. Verificar
BASE_URL=http://localhost:8000 ./scripts/smoke-test-prod.sh
```

---

## 📝 Notas Importantes

- **Permisos:** Todos los scripts deben ser ejecutables (`chmod +x scripts/*.sh`)
- **Variables de entorno:** Los scripts asumen que `.env` está en la raíz del proyecto
- **Backups:** Se guardan automáticamente en `backups/` antes de cada deploy
- **Logs:** Todos los scripts usan colores para mejor legibilidad
- **Exit codes:** 0 = éxito, 1 = error (útil para CI/CD)

---

## 🔧 Personalización

Para adaptar los scripts a tu entorno:

1. **pre-deploy-check.sh:** Agregar validaciones específicas en la sección correspondiente
2. **smoke-test-prod.sh:** Agregar tests adicionales con `run_test "nombre" "comando"`
3. **deploy.sh:** Modificar URLs y puertos según tu configuración

---

## 📞 Troubleshooting

### Script falla con "permission denied"
```bash
chmod +x scripts/*.sh
```

### pre-deploy-check.sh reporta errores en desarrollo
Normal. El script está optimizado para producción. En desarrollo algunos checks pueden dar warnings.

### smoke-test-prod.sh falla con "connection refused"
Verificar que el sistema esté corriendo:
```bash
docker-compose -f backend/docker-compose.yml ps
```

### deploy.sh falla en migraciones
Las migraciones pueden fallar si ya están aplicadas (esto es normal). Si es un error real, revisar:
```bash
docker-compose -f backend/docker-compose.yml logs app
```

---

Para más información, consultar:
- `../PRODUCTION_SETUP.md` - Guía completa de producción
- `../STATUS_ACTUAL_2025-10-02.md` - Estado actual del proyecto
- `../backend/deploy.sh` - Script de deploy original (más completo, incluye SSL)
