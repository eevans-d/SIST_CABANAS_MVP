# 🔑 RESUMEN EJECUTIVO: Credenciales Necesarias

**Sistema MVP - Automatización de Reservas**
**Para obtener ANTES de Deploy**

---

## 📊 TABLA DE VALORES NECESARIOS

### GENERAR (Auto-generado - Ejecutar scripts)

| # | Variable | Tipo | Tamaño | Script Generador | Crítica |
|---|----------|------|--------|------------------|---------|
| 1 | `JWT_SECRET` | Base64 | 48 chars | `secrets.token_urlsafe(48)` | 🔒 **SÍ** |
| 2 | `ICS_SALT` | Hex | 32 chars | `secrets.token_hex(16)` | 🔒 **SÍ** |
| 3 | `POSTGRES_PASSWORD` | Base64 | 32 chars | `openssl rand -base64 32` | 🔒 **SÍ** |
| 4 | `REDIS_PASSWORD` | Base64 | 32 chars | `openssl rand -base64 32` | 🔒 **SÍ** |
| 5 | `WHATSAPP_VERIFY_TOKEN` | Hex | 32 chars | `secrets.token_hex(16)` | 🔒 **SÍ** |
| 6 | `MERCADOPAGO_WEBHOOK_SECRET` | Base64 | 32 chars | `secrets.token_urlsafe(32)` | 🔒 **SÍ** |
| 7 | `GRAFANA_ADMIN_PASSWORD` | Base64 | 16 chars | `secrets.token_urlsafe(16)` | ⚠️ IMPORTANTE |

---

### OBTENER DE TERCEROS (Manual)

#### 🟦 META / WhatsApp Business

| # | Variable | Dónde Obtener | Formato | Crítica | Link |
|---|----------|---------------|---------|---------|------|
| 8 | `WHATSAPP_ACCESS_TOKEN` | Meta Dev Console | `EAAB...xxxxx` | 🔒 **SÍ** | [Meta Apps](https://developers.facebook.com/apps/) |
| 9 | `WHATSAPP_APP_SECRET` | Meta Dev Console | `abc123...def456` | 🔒 **SÍ** | Settings → Basic |
| 10 | `WHATSAPP_PHONE_ID` | Meta Dev Console | `15551234567` | 🔒 **SÍ** | WhatsApp → Phone Numbers |
| 11 | `WHATSAPP_BUSINESS_ACCOUNT_ID` | Meta Dev Console | `12345678901234` | 🔒 **SÍ** | WhatsApp → About |

**Pasos rápidos:**
1. https://developers.facebook.com/apps/ → Login
2. Seleccionar app → WhatsApp
3. Settings → Copiar App Secret
4. Getting Started → Copiar Access Token
5. Phone Numbers → Copiar Phone ID
6. About → Copiar Business Account ID

---

#### 💰 MERCADO PAGO

| # | Variable | Dónde Obtener | Formato | Crítica | Link |
|---|----------|---------------|---------|---------|------|
| 12 | `MERCADOPAGO_ACCESS_TOKEN` | MP Developer | `APP_USR-xxxxx...` | 🔒 **SÍ** | [MP Dev](https://www.mercadopago.com.ar/developers/) |
| 13 | `MERCADOPAGO_PUBLIC_KEY` | MP Developer | `APP_USR-xxxxx...` | ⚠️ IMPORTANTE | [MP Dev](https://www.mercadopago.com.ar/developers/) |

**Pasos rápidos:**
1. https://www.mercadopago.com.ar/developers/ → Login con MP account
2. Mis aplicaciones → [Tu App Nombre]
3. Credenciales → Tab PRODUCCIÓN (no Sandbox)
4. Copiar Access Token + Public Key

---

#### 📧 GMAIL (SMTP/IMAP)

| # | Variable | Dónde Obtener | Formato | Crítica |
|---|----------|---------------|---------|---------|
| 14 | `SMTP_USER` | Gmail | `tu@gmail.com` | 🔒 **SÍ** |
| 15 | `SMTP_PASSWORD` | Gmail App Password | `xxxx xxxx xxxx xxxx` | 🔒 **SÍ** |
| 16 | `IMAP_USER` | Gmail | `tu@gmail.com` | 🔒 **SÍ** |
| 17 | `IMAP_PASSWORD` | Gmail App Password | `xxxx xxxx xxxx xxxx` | 🔒 **SÍ** |

**Pasos rápidos:**
1. https://myaccount.google.com/ → Login
2. Security → 2-Step Verification (activar si no está)
3. Security → App passwords
4. Seleccionar: Mail, Windows Computer
5. Copiar contraseña generada (16 caracteres)
6. Usar mismo password para SMTP y IMAP

---

### CONFIGURAR (Tu entorno)

| # | Variable | Valor | Ejemplo | Crítica |
|---|----------|-------|---------|---------|
| 18 | `DOMAIN` | Tu dominio | `api.reservas.tudominio.com` | 🔒 **SÍ** |
| 19 | `BASE_URL` | URL completa | `https://api.reservas.tudominio.com` | 🔒 **SÍ** |
| 20 | `ENVIRONMENT` | Ambiente | `production` | 🔒 **SÍ** |
| 21 | `ALLOWED_ORIGINS` | CORS domains | `https://admin.tudominio.com,https://reservas.tudominio.com` | ⚠️ IMPORTANTE |
| 22 | `ADMIN_ALLOWED_EMAILS` | Admin emails | `admin@tudominio.com` | ⚠️ IMPORTANTE |
| 23 | `SMTP_FROM_EMAIL` | Email from | `reservas@tudominio.com` | ⚠️ IMPORTANTE |

---

## 🎯 GENERADOR DE SECRETOS

Ejecutar en terminal para generar todos de una vez:

```bash
#!/bin/bash
echo "=== GENERANDO SECRETOS PARA PRODUCCIÓN ==="
echo ""

JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
echo "JWT_SECRET=$JWT_SECRET"

ICS_SALT=$(python3 -c "import secrets; print(secrets.token_hex(16))")
echo "ICS_SALT=$ICS_SALT"

POSTGRES_PASSWORD=$(openssl rand -base64 32)
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"

REDIS_PASSWORD=$(openssl rand -base64 32)
echo "REDIS_PASSWORD=$REDIS_PASSWORD"

WHATSAPP_VERIFY_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(16))")
echo "WHATSAPP_VERIFY_TOKEN=$WHATSAPP_VERIFY_TOKEN"

MERCADOPAGO_WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "MERCADOPAGO_WEBHOOK_SECRET=$MERCADOPAGO_WEBHOOK_SECRET"

GRAFANA_ADMIN_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD"

echo ""
echo "✅ Copiar todos estos valores a .env"
```

**Guardar output en lugar seguro (1Password, LastPass, Vault)** 🔒

---

## 📋 CHECKLIST RÁPIDO (Orden de Tareas)

### Semana 1: Generación de Secretos
- [ ] Ejecutar script generador arriba
- [ ] Guardar todos los valores en lugar seguro
- [ ] Crear `.env` desde template

### Semana 2: Obtener Meta/WhatsApp
- [ ] Crear Meta Business Account
- [ ] Crear App WhatsApp
- [ ] Obtener `WHATSAPP_ACCESS_TOKEN`
- [ ] Obtener `WHATSAPP_APP_SECRET`
- [ ] Obtener `WHATSAPP_PHONE_ID`
- [ ] Obtener `WHATSAPP_BUSINESS_ACCOUNT_ID`
- [ ] Validar con: `curl -X GET "https://graph.instagram.com/me/whatsapp_business_accounts?access_token=TOKEN"`

### Semana 2: Obtener Mercado Pago
- [ ] Ir a https://www.mercadopago.com.ar/developers/
- [ ] Crear/seleccionar App
- [ ] Obtener `MERCADOPAGO_ACCESS_TOKEN` (PRODUCCIÓN)
- [ ] Obtener `MERCADOPAGO_PUBLIC_KEY` (PRODUCCIÓN)
- [ ] Validar con: `curl -X GET "https://api.mercadopago.com/v1/payments?access_token=TOKEN"`

### Semana 2: Configurar Email
- [ ] Crear Gmail (o usar existente)
- [ ] Activar 2FA en Gmail
- [ ] Generar App Password
- [ ] Validar SMTP con Python
- [ ] Validar IMAP con Python

### Semana 3: Pre-Deploy
- [ ] Llenar `.env` completo
- [ ] Validar con: `docker-compose up`
- [ ] Validar health: `curl https://domain/api/v1/healthz`
- [ ] Configurar Webhooks en Meta
- [ ] Configurar Webhooks en MP

---

## ✅ TEMPLATE .env MÍNIMO

```env
# CRÍTICAS - GENERAR
JWT_SECRET=<GENERAR>
ICS_SALT=<GENERAR>
POSTGRES_PASSWORD=<GENERAR>
REDIS_PASSWORD=<GENERAR>
WHATSAPP_VERIFY_TOKEN=<GENERAR>
MERCADOPAGO_WEBHOOK_SECRET=<GENERAR>
GRAFANA_ADMIN_PASSWORD=<GENERAR>

# CRÍTICAS - OBTENER
WHATSAPP_ACCESS_TOKEN=<OBTENER DE META>
WHATSAPP_APP_SECRET=<OBTENER DE META>
WHATSAPP_PHONE_ID=<OBTENER DE META>
WHATSAPP_BUSINESS_ACCOUNT_ID=<OBTENER DE META>
MERCADOPAGO_ACCESS_TOKEN=<OBTENER DE MP>
MERCADOPAGO_PUBLIC_KEY=<OBTENER DE MP>
SMTP_USER=<TU EMAIL GMAIL>
SMTP_PASSWORD=<GMAIL APP PASSWORD>
IMAP_USER=<TU EMAIL GMAIL>
IMAP_PASSWORD=<GMAIL APP PASSWORD>

# IMPORTANTES - CONFIGURAR
DOMAIN=<TU DOMINIO>
BASE_URL=https://<TU DOMINIO>
ENVIRONMENT=production
ALLOWED_ORIGINS=https://<TU DOMINIO>
ADMIN_ALLOWED_EMAILS=admin@tudominio.com
SMTP_FROM_EMAIL=reservas@tudominio.com

# AUTOMÁTICAS
DATABASE_URL=postgresql+asyncpg://alojamientos:$POSTGRES_PASSWORD@postgres:5432/alojamientos_db
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0
```

---

## 🚨 NO OLVIDAR

```
❌ NO commitear .env a git
❌ NO compartir credenciales por Slack/Email
❌ NO usar credenciales Sandbox en producción
✅ GUARDAR .env en 1Password/LastPass
✅ CAMBIAR JWT_SECRET cada 90 días
✅ VALIDAR TODOS los valores antes de deploy
✅ USAR HTTPS con Let's Encrypt
```

---

**Total valores necesarios: 23**
**Generados automáticamente: 7**
**Obtener de terceros: 11**
**Configurar del entorno: 5**

**Tiempo estimado: 2-3 horas (si cuentas de servicios ya existen)**
