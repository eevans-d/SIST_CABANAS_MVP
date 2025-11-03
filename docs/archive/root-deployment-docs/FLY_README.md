> Documento unificado: usa estas guías canónicas. Este archivo fue simplificado para evitar duplicados.

# 🚀 Deploy en Fly.io — Referencias canónicas

Para despliegues en Fly.io utiliza:

- `DEPLOY_FAST_TRACK.md` (resumen rápido)
- `ops/STAGING_DEPLOYMENT_QUICK_START.md` (paso a paso)
- `ops/staging-deploy-interactive.sh` (guiado)
- `ops/FLY_DEPLOYMENT_GUIDE.md` (detallado)
- `ops/FLY_DEPLOY_CHECKLIST.md` (checklist)

Recordatorio:
- App única: `sist-cabanas-mvp` en `gru`
- Ejecuta `./ops/deploy-check.sh` antes de cualquier `fly deploy`

Índice completo: `DOCUMENTATION_INDEX.md`.
2. Crea un proyecto Redis en región `us-east-1` (latencia baja)
3. Copia la URL: `redis://:password@host:port`

**Opción B**: Via Fly extensiones (recomendado)
```bash
# Nota: Esta característica puede variar según plan
# Para MVP, Upstash gratuito es suficiente
```

### 5. Configurar Secretos

```bash
# Copiar variables de .env.template a .env local
cp .env.template .env

# Luego, configurar secretos en Fly.io
flyctl secrets set \
  DATABASE_URL="postgresql://app:password@sist-cabanas-db.internal:5432/postgres" \
  REDIS_URL="redis://:password@host:port/0" \
  JWT_SECRET="P9LQYGSuJVjvdJSrJ3sS-MjLEMJXVFWVaq1uA4Z2FLw" \
  WHATSAPP_ACCESS_TOKEN="your_whatsapp_token" \
  WHATSAPP_APP_SECRET="your_whatsapp_secret" \
  WHATSAPP_PHONE_ID="your_phone_id" \
  MERCADOPAGO_ACCESS_TOKEN="your_mp_token"
```

### 6. Deploy

```bash
# Deployprimera vez (crea app)
flyctl launch
# Selecciona:
# - App name: sist-cabanas-mvp
# - Region: eze (Buenos Aires)
# - Deploy now: yes

# Deploys posteriores
flyctl deploy

# Ver logs
flyctl logs -a sist-cabanas-mvp

# Abrir app
flyctl open -a sist-cabanas-mvp
```

## 🎯 Validación

### 1. Health Check

```bash
# Debe responder 200 OK
curl https://sist-cabanas-mvp.fly.dev/api/v1/healthz

# Respuesta esperada:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok", "latency_ms": 45},
    "redis": {"status": "ok", "latency_ms": 12},
    "ical_sync": {"status": "ok", "last_sync_minutes": 2}
  }
}
```

### 2. Crear Reserva de Prueba

```bash
curl -X POST https://sist-cabanas-mvp.fly.dev/api/v1/reservations \
  -H "Content-Type: application/json" \
  -d '{
    "accommodation_id": 1,
    "check_in": "2025-11-20",
    "check_out": "2025-11-23",
    "guests": 2,
    "contact_name": "Test User",
    "contact_phone": "+5491155443322",
    "contact_email": "test@example.com",
    "channel": "web"
  }'
```

### 3. Ver Métricas

```bash
# Prometheus metrics (port 9090 si está expuesto)
curl https://sist-cabanas-mvp.fly.dev/metrics | head -30
```

## 🛑 Troubleshooting

### App no arranca

```bash
# Ver logs en tiempo real
flyctl logs -a sist-cabanas-mvp -f

# Buscar errores
flyctl logs -a sist-cabanas-mvp | grep ERROR
```

### Database connection refused

```bash
# Verificar que DATABASE_URL es correcto
flyctl secrets list -a sist-cabanas-mvp | grep DATABASE

# Probar conexión
flyctl proxy 5432:5432 -a sist-cabanas-mvp-db
psql "postgresql://app:password@localhost/postgres"
```

### Redis timeout

```bash
# Verificar REDIS_URL
flyctl secrets list -a sist-cabanas-mvp | grep REDIS

# Probar conexión (desde app)
flyctl ssh console -a sist-cabanas-mvp
python3 -c "import redis; redis.Redis.from_url('redis://...').ping()"
```

### Out of memory (OOM)

```bash
# Aumentar RAM
flyctl scale memory 512 -a sist-cabanas-mvp

# O cambiar instancia
flyctl scale vm shared-cpu-2x -a sist-cabanas-mvp
```

## 📊 Monitoreo

### Dashboard Fly.io

```bash
# Abrir dashboard
flyctl dashboard -a sist-cabanas-mvp

# O en navegador:
# https://fly.io/apps/sist-cabanas-mvp
```

### Logs en Tiempo Real

```bash
# Todos los logs
flyctl logs -a sist-cabanas-mvp -f

# Solo errores
flyctl logs -a sist-cabanas-mvp | grep -i error

# Últimas 100 líneas
flyctl logs -a sist-cabanas-mvp --lines 100
```

### SSH a Instancia

```bash
# Entrar en console
flyctl ssh console -a sist-cabanas-mvp

# Ejecutar comando
flyctl ssh console -a sist-cabanas-mvp --command "python3 -c 'print(1)'"
```

## 🔄 Deploys

### Deploy Manual

```bash
# Cambios locales
git add -A
git commit -m "fix: something"

# Deploy
flyctl deploy

# Seguir progreso
flyctl logs -a sist-cabanas-mvp -f
```

### CI/CD con GitHub Actions

Ver `FLY_DEPLOYMENT_GUIDE.md` para configurar GitHub Actions.

## 🔐 Secrets & Variables

### Secrets (secretos)

```bash
# Crear secreto
flyctl secrets set JWT_SECRET="new_value"

# Ver secretos (sin valores)
flyctl secrets list

# Actualizar secreto
flyctl secrets set JWT_SECRET="updated_value"

# Borrar secreto
flyctl secrets unset JWT_SECRET
```

### Variables de Entorno (públicas)

```bash
# En fly.toml ya están configuradas:
[env]
  ENVIRONMENT = "production"
  PORT = "8080"
  # ...
```

## 📋 Checklist Pre-Producción

- [ ] Base de datos migrada: `alembic upgrade head` ejecutado
- [ ] Health check responde 200 OK
- [ ] Webhooks (WhatsApp, Mercado Pago) funcionan
- [ ] iCal sync sincroniza correctamente
- [ ] Reservas se crean sin errores
- [ ] Logs sin ERROR ni WARNING sospechosos
- [ ] Métricas en `/metrics` accesibles
- [ ] Dashboard admin carga correctamente
- [ ] HTTPS activo y certificado válido

## 🎓 Recursos

- **Fly.io Docs**: https://fly.io/docs/
- **Fly.io Python**: https://fly.io/docs/languages-and-frameworks/python/
- **Upstash Redis**: https://upstash.com/docs/redis/features/python
- **PostgreSQL en Fly.io**: https://fly.io/docs/postgres/
- **GitHub Actions**: https://docs.github.com/en/actions

## 🆘 Soporte

### Comandos Útiles

```bash
# Ver estado de la app
flyctl status -a sist-cabanas-mvp

# Listar máquinas
flyctl machines list -a sist-cabanas-mvp

# Ver detalles de máquina
flyctl machines show <id> -a sist-cabanas-mvp

# Restart app
flyctl restart -a sist-cabanas-mvp

# Scale workers
flyctl scale count 2 -a sist-cabanas-mvp
```

### Contactos

- **Fly.io Support**: https://fly.io/support
- **Documentación Completa**: Consulta `FLY_DEPLOYMENT_GUIDE.md`

---

**Última actualización**: Octubre 2025
**Versión**: 1.0 - MVP
**Región**: eze (Buenos Aires, Argentina)
