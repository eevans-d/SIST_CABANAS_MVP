# 🚂 Deploy en Railway - Guía Rápida

> **Estado**: ✅ Configurado y listo para deploy en Railway.app

## ⚡ Deploy en 5 Minutos

### 1️⃣ Crear Proyecto en Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Click en "Deploy on Railway"
2. Conecta tu cuenta de GitHub
3. Selecciona repositorio: `SIST_CABANAS_MVP`
4. Railway detectará automáticamente:
   - ✅ `Procfile` → Comando de inicio
   - ✅ `railway.toml` → Configuración
   - ✅ `backend/Dockerfile` → Build instructions

### 2️⃣ Agregar Bases de Datos

En tu proyecto Railway:

**PostgreSQL:**
1. Click "+ New" → "Database" → "PostgreSQL"
2. Railway auto-configura `DATABASE_URL` ✅

**Redis:**
1. Click "+ New" → "Database" → "Redis"
2. Railway auto-configura `REDIS_URL` ✅

### 3️⃣ Configurar Variables de Entorno

En el servicio backend → "Variables" → Agregar:

```bash
# 🔐 Seguridad (REQUERIDO)
JWT_SECRET=generar_con_openssl_rand_hex_32
ENVIRONMENT=production

# 📱 WhatsApp Business (REQUERIDO)
WHATSAPP_ACCESS_TOKEN=tu_token_aqui
WHATSAPP_APP_SECRET=tu_secret_aqui
WHATSAPP_PHONE_ID=tu_phone_id_aqui
WHATSAPP_VERIFY_TOKEN=tu_verify_token_aqui

# 💳 Mercado Pago (REQUERIDO)
MERCADOPAGO_ACCESS_TOKEN=tu_token_aqui
MERCADOPAGO_WEBHOOK_SECRET=tu_secret_aqui

# 👤 Admin (REQUERIDO)
ADMIN_ALLOWED_EMAILS=tu_email@example.com
```

### 4️⃣ Deploy

1. Click "Deploy" en Railway
2. Espera ~5-7 minutos (build + migraciones)
3. Verifica health check: `https://tu-app.up.railway.app/api/v1/healthz`

### 5️⃣ Configurar Webhooks

Una vez desplegado, configura en servicios externos:

**WhatsApp Webhook:**
```
URL: https://tu-app.up.railway.app/api/v1/webhooks/whatsapp
Verify Token: [tu WHATSAPP_VERIFY_TOKEN]
```

**Mercado Pago Webhook:**
```
URL: https://tu-app.up.railway.app/api/v1/mercadopago/webhook
```

---

## 📚 Documentación Completa

- **Guía Detallada**: [`docs/operations/RAILWAY_DEPLOYMENT_GUIDE.md`](docs/operations/RAILWAY_DEPLOYMENT_GUIDE.md)
- **Troubleshooting**: Ver sección en guía completa
- **Variables de entorno**: Ver `.env.template`

---

## 🔧 Archivos de Configuración Railway

Este repositorio incluye:

| Archivo | Propósito |
|---------|-----------|
| `Procfile` | Define comando de inicio para Railway |
| `railway.toml` | Configuración explícita de build/deploy |
| `backend/start-railway.sh` | Script de inicio optimizado |
| `backend/Dockerfile` | Build instructions |

---

## ⚠️ Problemas Comunes

### Build falla con "Missing start command"

✅ **Ya solucionado**: Ahora tenemos `Procfile` y `railway.toml`

### Build exitoso pero app no inicia

**Verificar:**
1. Todas las variables de entorno configuradas
2. PostgreSQL y Redis estén UP
3. Logs en Railway UI

### Database migrations fallan

**Verificar:**
1. `DATABASE_URL` auto-configurada por Railway
2. Servicio PostgreSQL está activo
3. Permisos de base de datos

---

## 💰 Costos Estimados

**Plan Hobby**: ~$5-10 USD/mes
- Backend: $5/mes
- PostgreSQL: Incluido
- Redis: Incluido

**Plan Pro**: ~$20 USD/mes (para escalar)

---

## 🎯 Próximos Pasos Post-Deploy

1. ✅ Configurar dominio custom
2. ✅ Deploy frontend (Vercel/Netlify)
3. ✅ Configurar webhooks externos
4. ✅ Monitoreo y alertas
5. ✅ Backups automáticos

---

## 🆘 Soporte

- 📖 Railway Docs: https://docs.railway.app
- 💬 Railway Discord: https://discord.gg/railway
- 📧 Soporte proyecto: Ver `README.md`

---

**Última actualización**: Octubre 18, 2025
**Estado**: ✅ Listo para producción
