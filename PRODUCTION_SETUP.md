# 🚀 Configuración para Producción

Este documento detalla los pasos específicos para preparar el sistema para deploy en producción.

## ✅ Pre-requisitos Cumplidos

- [x] Tests en verde (37 passed, 11 skipped)
- [x] `.env.template` completo y documentado
- [x] docker-compose sintácticamente correcto
- [x] Puertos DB/Redis **comentados** para seguridad
- [x] Template de Nginx con variables de entorno

## 🔧 Configuración Paso a Paso

### 1. Preparar Variables de Entorno

```bash
# Copiar template y completar valores productivos
cp .env.template .env

# Editar .env con valores reales
nano .env
```

**Variables críticas a configurar:**
- `DOMAIN`: Tu dominio real (ej: `alojamientos.tuempresa.com`)
- `POSTGRES_PASSWORD`: Password seguro de DB
- `REDIS_PASSWORD`: Password seguro de Redis
- `JWT_SECRET`: Secret aleatorio largo (min 32 chars)
- `ICS_SALT`: Salt aleatorio para tokens iCal
- `WHATSAPP_*`: Credenciales de Meta Business
- `MERCADOPAGO_*`: Access token de Mercado Pago
- `SMTP_*`: Configuración de email

### 2. Generar Configuración de Nginx

```bash
cd backend

# Generar nginx.conf desde template
./generate_nginx_conf.sh ../.env

# Verificar resultado
cat nginx.conf | grep server_name
# Debe mostrar: server_name tu-dominio.com;
```

### 3. Configurar SSL Certificates

**Opción A: Let's Encrypt (Recomendado)**

```bash
# Ejecutar script de deploy que incluye certbot
./deploy.sh
```

**Opción B: Certificados propios**

```bash
# Copiar certificados a nginx/ssl/
mkdir -p nginx/ssl
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/
chmod 600 nginx/ssl/privkey.pem
```

### 4. Configurar Webhooks

**WhatsApp Business:**
1. Ir a Meta Developer Console
2. Configurar webhook URL: `https://TU-DOMINIO/api/v1/webhooks/whatsapp`
3. Usar `WHATSAPP_VERIFY_TOKEN` del .env
4. Suscribirse a eventos: `messages`, `message_status`

**Mercado Pago:**
1. Ir a Panel de Mercado Pago
2. Configurar webhook URL: `https://TU-DOMINIO/api/v1/webhooks/mercadopago`
3. Suscribirse a eventos de pagos

### 5. Deploy

```bash
# Levantar servicios
docker-compose up -d

# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f api

# Ejecutar migraciones
docker-compose exec api alembic upgrade head
```

### 6. Verificación Post-Deploy

```bash
# Health check
curl https://TU-DOMINIO/api/v1/healthz

# Debe retornar: {"status":"healthy", ...}

# Verificar métricas (opcional)
curl https://TU-DOMINIO/metrics
```

### 7. Smoke Tests en Producción

```bash
# Desde tu máquina local con .env productivo
export ENVIRONMENT=production
pytest backend/tests/test_journey_basic.py -v
```

## 🔒 Seguridad Post-Deploy

### Puertos Expuestos

**✅ Configuración actual (segura):**
- Puerto 80 (HTTP) → Redirect a HTTPS
- Puerto 443 (HTTPS) → Nginx reverse proxy
- Puertos 5432 (PostgreSQL) y 6379 (Redis) → **COMENTADOS** (solo red interna)

**Para debugging temporal:**
Si necesitás acceso directo a DB/Redis, descomentá temporalmente en `docker-compose.yml`:
```yaml
db:
  ports:
    - "127.0.0.1:5432:5432"  # Solo localhost
```

### Rate Limiting Activo

- API general: 10 req/s por IP
- Webhooks: 50 req/s por IP
- Health checks: sin límite

### Protección Adicional Recomendada

1. **Firewall del servidor:**
```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

2. **Fail2ban** para protección DDoS:
```bash
apt install fail2ban
# Configurar reglas para Nginx
```

3. **Monitoreo:**
```bash
# Instalar y configurar Prometheus + Grafana
# El endpoint /metrics ya está expuesto
```

## 📊 Monitoreo

### Métricas Disponibles

- `reservations_created_total`
- `reservations_confirmed_total`
- `ical_last_sync_age_minutes`
- Métricas HTTP de FastAPI Instrumentator

### Health Check

```bash
# Healthcheck completo con detalles
curl -s https://TU-DOMINIO/api/v1/healthz | jq

# Monitoreo periódico (cron)
*/5 * * * * curl -sf https://TU-DOMINIO/api/v1/healthz || echo "Health check failed"
```

## 🔄 Backup y Rollback

### Backup Automático

El script `deploy.sh` incluye:
- Backup automático de DB antes de migraciones
- Snapshot de código en `/opt/alojamientos/backups/`

### Rollback Manual

```bash
# Restaurar backup de DB
docker-compose exec db psql -U alojamientos -d alojamientos_db < backup.sql

# Volver a versión anterior
git checkout <commit-anterior>
docker-compose up -d --build
```

## 📝 Checklist Final Pre-Producción

- [ ] .env configurado con valores productivos
- [ ] nginx.conf generado con dominio real
- [ ] Certificados SSL válidos
- [ ] Webhooks configurados en Meta y Mercado Pago
- [ ] Health check responde OK
- [ ] Métricas accesibles
- [ ] Firewall configurado
- [ ] Backup automático funcionando
- [ ] Logs estructurados funcionando
- [ ] Smoke tests en producción pasando

## 🆘 Troubleshooting

### Nginx no arranca
```bash
# Validar sintaxis
docker-compose exec nginx nginx -t

# Ver logs
docker-compose logs nginx
```

### DB connection failed
```bash
# Verificar variables de entorno
docker-compose exec api env | grep DB

# Verificar conectividad desde app
docker-compose exec api nc -zv db 5432
```

### Webhooks no llegan
```bash
# Ver logs de API
docker-compose logs -f api | grep webhook

# Verificar firmas están habilitadas
grep WHATSAPP_APP_SECRET .env
```

## 📞 Soporte

Para issues de producción:
1. Revisar logs: `docker-compose logs -f api`
2. Verificar health: `curl /api/v1/healthz`
3. Consultar métricas: `curl /metrics`
4. Abrir issue en repo con logs relevantes
