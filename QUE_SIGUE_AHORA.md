# 📋 QUÉ SIGUE - Sistema MVP Alojamientos

**Actualizado:** 9 de Octubre de 2025
**Estado Sistema:** ✅ FUNCIONANDO CON SECRETOS SEGUROS
**Próximo Milestone:** Configuración para Producción

---

## 🎯 TAREAS INMEDIATAS (2-3 horas)

### 1. 🔒 CONFIGURAR HTTPS/SSL (BLOQUEANTE)
**Tiempo estimado:** 1-2 horas
**Prioridad:** CRÍTICA

```bash
# Requisitos previos:
# 1. Tener un dominio real (ej: miempresa.com)
# 2. DNS configurado apuntando al servidor
# 3. Puertos 80 y 443 abiertos en firewall

# Pasos:
cd /home/eevan/ProyectosIA/SIST_CABAÑAS
./scripts/setup_ssl.sh

# O manual:
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

### 2. 📱 ACTIVAR WHATSAPP BUSINESS API  
**Tiempo estimado:** 1 hora
**Prioridad:** CRÍTICA

```bash
# 1. En Meta Business Manager (business.facebook.com):
#    - Crear app de WhatsApp Business
#    - Configurar webhook:
#      URL: https://tu-dominio.com/api/v1/webhooks/whatsapp
#      Verify Token: JpRq-nmkfNTY5rALzgFGrGgD_LJLKvxqUKEp4ma3ZDA
#    - Obtener tokens

# 2. Actualizar .env:
WHATSAPP_ACCESS_TOKEN=tu_token_aqui
WHATSAPP_APP_SECRET=tu_app_secret_aqui  
WHATSAPP_PHONE_ID=tu_phone_id_aqui

# 3. Reiniciar
docker-compose restart api
```

### 3. 💰 CONFIGURAR MERCADO PAGO
**Tiempo estimado:** 30 minutos  
**Prioridad:** CRÍTICA

```bash
# 1. En developers.mercadopago.com:
#    - Crear aplicación
#    - Obtener credenciales de producción/sandbox

# 2. Actualizar .env:
MERCADOPAGO_ACCESS_TOKEN=tu_access_token_aqui
MERCADOPAGO_PUBLIC_KEY=tu_public_key_aqui

# 3. Webhook ya configurado:
# Secret: sS5zRKswMiOBW_sZdrJdsGCCMbgLNsCz_f3x_7tnNf4
# URL: https://tu-dominio.com/api/v1/webhooks/mercadopago
```

### 4. 🌐 CONFIGURAR DOMINIO DE PRODUCCIÓN
**Tiempo estimado:** 15 minutos
**Prioridad:** ALTA

```bash
# Actualizar .env:
DOMAIN=tu-dominio-real.com
BASE_URL=https://tu-dominio-real.com  
ENVIRONMENT=production

# Reiniciar servicios
docker-compose restart
```

---

## 🔧 TAREAS DE HARDENING (Opcional pero recomendado)

### Seguridad Adicional
```bash
# 1. Cerrar puertos de desarrollo en docker-compose.yml
# Comentar las líneas:
# postgres:
#   ports:
#     - "5433:5432"  # ← Comentar esta línea
# redis:  
#   ports:
#     - "6379:6379"  # ← Comentar esta línea

# 2. Configurar firewall
sudo ufw allow 80
sudo ufw allow 443  
sudo ufw allow 22
sudo ufw --force enable

# 3. Configurar backup automático
./scripts/setup_backup.sh
```

---

## 📊 VERIFICACIÓN POST-CONFIGURACIÓN

### Test Completo del Sistema
```bash
# 1. Health check
curl -s https://tu-dominio.com/api/v1/healthz

# 2. Test de pre-reserva
curl -X POST https://tu-dominio.com/api/v1/reservations/pre-reserve \
  -H "Content-Type: application/json" \
  -d '{
    "accommodation_id": 1,
    "check_in": "2025-10-15", 
    "check_out": "2025-10-17",
    "guests": 2,
    "contact_name": "Test User",
    "contact_phone": "+5491123456789",
    "channel": "whatsapp"
  }'

# 3. Test de webhook WhatsApp
# (Se verifica cuando Meta envíe el primer mensaje)

# 4. Test de webhook Mercado Pago  
# (Se verifica con primer pago de prueba)
```

### Métricas Esperadas (POST-configuración)
```json
{
  "status": "healthy",  // ← Debe cambiar de "degraded" a "healthy"
  "database": {"status": "ok"},
  "redis": {"status": "ok"}, 
  "ical": {"status": "ok"},
  "whatsapp": {"status": "ok"},      // ← Debe cambiar
  "mercadopago": {"status": "ok"},   // ← Debe cambiar
  "runtime": {"status": "ok"}
}
```

---

## 🚀 SIGUIENTE FASE: CONTENIDO Y TESTING

Una vez completadas las tareas anteriores:

### 1. Crear Contenido de Prueba
```bash
# Ejecutar script de datos de ejemplo
docker-compose exec api python scripts/seed.py
```

### 2. Testing E2E Completo  
```bash
# Ejecutar suite completa de validación
./execute_validation_plan.sh
```

### 3. Monitoreo y Ajustes
- Configurar alertas de Prometheus
- Ajustar rate limits según uso real
- Optimizar tamaños de pool de DB según carga

---

## 💡 NOTAS IMPORTANTES

- **Backup:** Configurar antes del primer uso en producción
- **Monitoring:** Las métricas están en `/metrics` para Prometheus
- **Logs:** Todos los logs están en formato JSON estructurado
- **Escalabilidad:** Sistema diseñado para escalar horizontalmente
- **Seguridad:** Anti-doble-booking está validado y funcionando

**Estado actual:** Sistema listo para configuración de producción 🎉