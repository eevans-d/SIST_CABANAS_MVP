# ✅ Deploy Checklist - Sistema Alojamientos MVP

**Fecha de deploy:** _______________
**Versión:** v1.0.0
**Responsable:** _______________

## 🔍 Pre-Deploy Checklist

### Configuración
- [ ] **Archivo .env creado** desde .env.template
- [ ] **POSTGRES_PASSWORD** cambiado del valor por defecto
- [ ] **REDIS_PASSWORD** cambiado del valor por defecto
- [ ] **JWT_SECRET** generado con `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] **ICS_SALT** generado con `python -c "import secrets; print(secrets.token_hex(16))"`
- [ ] **WHATSAPP_ACCESS_TOKEN** configurado desde Meta Developer
- [ ] **WHATSAPP_APP_SECRET** configurado desde Meta Developer
- [ ] **MERCADOPAGO_ACCESS_TOKEN** configurado desde MP Dashboard
- [ ] **MERCADOPAGO_WEBHOOK_SECRET** configurado (opcional pero recomendado)
- [ ] **DOMAIN** configurado en .env (sin https://)
- [ ] **EMAIL** configurado para Let's Encrypt

### Sistema
- [ ] **Docker** instalado (versión >= 20.10)
- [ ] **Docker Compose** instalado (versión >= 2.0)
- [ ] **Certificados SSL** directorio ./ssl creado
- [ ] **Firewall** configurado (puertos 80, 443 abiertos)
- [ ] **DNS** apuntando al servidor (A record)
- [ ] **Espacio en disco** suficiente (>10GB recomendado)

### Tests
- [ ] **Tests locales** pasando: `pytest -q`
- [ ] **Health endpoint** funcionando: `curl localhost:8000/health`
- [ ] **Database migrations** aplicadas: `alembic upgrade head`
- [ ] **Load test** exitoso: `python scripts/load_smoke.py`

## 🚀 Deploy Process

### Paso 1: Validación
```bash
./deploy.sh status
```
- [ ] **Comando ejecutado** sin errores
- [ ] **Variables verificadas** correctamente

### Paso 2: SSL Setup
```bash
./deploy.sh deploy
```
- [ ] **Certificados temporales** generados
- [ ] **Let's Encrypt** certificados obtenidos
- [ ] **Nginx** configurado correctamente

### Paso 3: Services Up
- [ ] **PostgreSQL** healthy: `docker-compose ps`
- [ ] **Redis** healthy: `docker-compose ps`
- [ ] **FastAPI** healthy: `docker-compose ps`
- [ ] **Nginx** healthy: `docker-compose ps`

### Paso 4: Health Verification
```bash
curl -f https://DOMAIN/health
```
- [ ] **Status: healthy** retornado
- [ ] **Database** connection OK
- [ ] **Redis** connection OK
- [ ] **All integrations** status verified

## 🔍 Post-Deploy Verification

### Endpoints Funcionales
- [ ] **https://DOMAIN/health** → 200 OK
- [ ] **https://DOMAIN/docs** → Swagger UI visible
- [ ] **https://DOMAIN/metrics** → 403 (solo desde localhost)
- [ ] **Webhook WhatsApp** configurado en Meta Developer
- [ ] **Webhook Mercado Pago** configurado en MP Dashboard

### Logs & Monitoring
```bash
docker-compose logs app | tail -20
```
- [ ] **No errores críticos** en logs
- [ ] **Structured logging** funcionando
- [ ] **Trace IDs** generándose correctamente
- [ ] **Sensitive data** enmascarada en logs

### Backup System
```bash
./deploy.sh backup
```
- [ ] **Backup script** ejecutado exitosamente
- [ ] **Crontab** configurado para backups diarios
- [ ] **Directorio backups** creado: `/opt/backups/alojamientos/`

### Performance Check
```bash
curl -w "@curl-format.txt" -s -o /dev/null https://DOMAIN/health
```
- [ ] **Response time** < 500ms
- [ ] **SSL handshake** < 100ms
- [ ] **Total time** < 1s

## 🚨 Rollback Plan

### Si algo falla:
```bash
./deploy.sh rollback
```
- [ ] **Comando documentado** y testado
- [ ] **Backup más reciente** identificado
- [ ] **Contacto técnico** disponible por 2 horas post-deploy

## 📋 Monitoring Setup

### Alerts (configurar post-deploy)
- [ ] **Health endpoint** monitoring (cada 5 min)
- [ ] **SSL certificate** expiration (30 días antes)
- [ ] **Disk space** monitoring (>80% alerta)
- [ ] **Error rate** monitoring (>5% crítico)

### Maintenance
- [ ] **SSL renewal** configurado: `./deploy.sh update-ssl`
- [ ] **Log rotation** configurado automáticamente
- [ ] **Database maintenance** programado (VACUUM, ANALYZE)

## 📞 Emergency Contacts

| Rol | Contacto | Disponibilidad |
|-----|----------|----------------|
| **Tech Lead** | _____________ | 24/7 primeras 48h |
| **DevOps** | _____________ | Horario laboral |
| **Product Owner** | _____________ | Notificación solamente |

## ✅ Sign-off

- [ ] **Deploy ejecutado** sin errores críticos
- [ ] **Health checks** pasando en producción
- [ ] **Backups** configurados y funcionando
- [ ] **Monitoring** básico activo
- [ ] **Rollback** plan verificado y documentado
- [ ] **Stakeholders** notificados del deploy exitoso

**Deploy completado por:** _______________
**Fecha/Hora:** _______________
**Notas adicionales:**
_____________________________
_____________________________

---

**🎉 MVP DEPLOYED SUCCESSFULLY! 🚀**
