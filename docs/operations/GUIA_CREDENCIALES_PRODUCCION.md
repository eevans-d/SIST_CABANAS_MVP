# 🔐 GUÍA COMPLETA: Credenciales, API Keys y Secrets para Producción
**Sistema MVP Automatización de Reservas**
**Fecha: 16 Octubre 2025**

---

## 📋 ÍNDICE RÁPIDO

1. [Variables Generadas Automáticamente](#1-variables-generadas-automáticamente)
2. [Credenciales de Terceros (Manual)](#2-credenciales-de-terceros-manual)
3. [URLs y Dominios](#3-urls-y-dominios)
4. [Base de Datos](#4-base-de-datos)
5. [Cache y Locks](#5-cache-y-locks)
6. [Email y SMTP](#6-email-y-smtp)
7. [Seguridad](#7-seguridad)
8. [Checklist de Obtención](#8-checklist-de-obtención)

---

## 1️⃣ VARIABLES GENERADAS AUTOMÁTICAMENTE

**Generar ANTES de llenar .env:**

```bash
# Ejecutar este script para generar todos los valores

# JWT Secret (48 caracteres base64)
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
echo "JWT_SECRET=$JWT_SECRET"

# iCal Salt (32 caracteres hex)
ICS_SALT=$(python3 -c "import secrets; print(secrets.token_hex(16))")
echo "ICS_SALT=$ICS_SALT"

# PostgreSQL Password
POSTGRES_PASSWORD=$(openssl rand -base64 32)
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"

# Redis Password
REDIS_PASSWORD=$(openssl rand -base64 32)
echo "REDIS_PASSWORD=$REDIS_PASSWORD"

# WhatsApp Verify Token (32 caracteres hex)
WHATSAPP_VERIFY_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(16))")
echo "WHATSAPP_VERIFY_TOKEN=$WHATSAPP_VERIFY_TOKEN"

# Mercado Pago Webhook Secret
MERCADOPAGO_WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "MERCADOPAGO_WEBHOOK_SECRET=$MERCADOPAGO_WEBHOOK_SECRET"

# Grafana Admin Password
GRAFANA_ADMIN_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD"
```

| Variable | Formato | Ejemplo | Seguridad |
|----------|---------|---------|-----------|
| `JWT_SECRET` | Base64 (48 chars) | `FqzT...xyz=` | 🔒 **CRÍTICA** |
| `ICS_SALT` | Hex (32 chars) | `a3f7b9c2e1d4...` | 🔒 **CRÍTICA** |
| `POSTGRES_PASSWORD` | Base64 (32 chars) | `K8p9...jK=` | 🔒 **CRÍTICA** |
| `REDIS_PASSWORD` | Base64 (32 chars) | `Qx2m...vL=` | 🔒 **CRÍTICA** |
| `WHATSAPP_VERIFY_TOKEN` | Hex (32 chars) | `c8d4a1f2...` | 🔒 **CRÍTICA** |
| `MERCADOPAGO_WEBHOOK_SECRET` | Base64 (32 chars) | `AbCd...XyZ=` | 🔒 **CRÍTICA** |
| `GRAFANA_ADMIN_PASSWORD` | Base64 (16 chars) | `qWe...Rty` | 🔒 **IMPORTANTE** |

---

## 2️⃣ CREDENCIALES DE TERCEROS (Manual)

### 🟦 **WhatsApp Business Cloud API**

**Dónde obtener:**
1. Ir a: https://www.facebook.com/login/
2. Acceder a: https://developers.facebook.com/apps/
3. Seleccionar tu app > WhatsApp > Configuración

| Variable | Descripción | Formato | Fuente |
|----------|-------------|---------|--------|
| `WHATSAPP_ACCESS_TOKEN` | Token de acceso API | `EAAB...xxxxx` | Meta Developer Console → WhatsApp → Tokens |
| `WHATSAPP_APP_SECRET` | Secret de la app | `abcd123def456` | Meta Developer Console → Settings → App Secrets |
| `WHATSAPP_PHONE_ID` | ID del número de teléfono | `15551234567` | Meta Developer Console → WhatsApp → Phone Numbers |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | ID de cuenta empresarial | `12345678901234` | Meta Developer Console → WhatsApp → About |

**Pasos detallados:**

```
1. Abrir: https://developers.facebook.com/apps

2. Seleccionar app > WhatsApp > Getting started

3. Copiar "Temporary access token":
   WHATSAPP_ACCESS_TOKEN=EAAB...

4. Ir a Settings > Basic:
   WHATSAPP_APP_SECRET=abc123...

5. WhatsApp > Phone Numbers:
   WHATSAPP_PHONE_ID=15551234567
   WHATSAPP_BUSINESS_ACCOUNT_ID=12345...

6. Validar token con curl:
   curl -X GET "https://graph.instagram.com/me/whatsapp_business_accounts?access_token=EAAB..."
```

**Token válido si responde:**
```json
{
  "data": [
    {
      "id": "12345678901234",
      "name": "Your Business Account"
    }
  ]
}
```

---

### 💰 **Mercado Pago**

**Dónde obtener:**
1. Ir a: https://www.mercadopago.com.ar/developers/es/
2. Acceder con tu cuenta de MP
3. Ir a: Aplicaciones > [Tu App] > Credenciales

| Variable | Descripción | Formato | Fuente |
|----------|-------------|---------|--------|
| `MERCADOPAGO_ACCESS_TOKEN` | Token de producción | `APP_USR-xxxxx...` | MP Dashboard → Credenciales → Access Token |
| `MERCADOPAGO_PUBLIC_KEY` | Clave pública | `APP_USR-xxxxx...` | MP Dashboard → Credenciales → Public Key |

**Pasos detallados:**

```
1. Ir a: https://www.mercadopago.com.ar/developers/es/

2. Hacer login con tu cuenta de MP

3. Ir a: Mis aplicaciones > [Tu App Nombre]

4. Seleccionar "Credenciales"

5. PRODUCCIÓN tab (no Sandbox):
   - Access Token: MERCADOPAGO_ACCESS_TOKEN=APP_USR-...
   - Public Key: MERCADOPAGO_PUBLIC_KEY=APP_USR-...

6. Validar token con curl:
   curl -X GET "https://api.mercadopago.com/v1/payments?access_token=APP_USR-..."
```

**Token válido si responde:**
```json
{
  "paging": {
    "total": 0,
    "limit": 0,
    "offset": 0
  },
  "results": []
}
```

---

### 📧 **Email (SMTP/IMAP)**

**Opción 1: Gmail**
```
1. Acceder a: https://myaccount.google.com/

2. Security > 2-Step Verification (activar si no está)

3. Security > App passwords (generar contraseña de app)

4. Seleccionar: Mail + Windows Computer

5. Copiar contraseña generada
```

| Variable | Gmail | Brevo | Otros |
|----------|-------|-------|-------|
| `SMTP_HOST` | `smtp.gmail.com` | `smtp-relay.brevo.com` | Según provider |
| `SMTP_PORT` | `587` | `587` | Según provider |
| `SMTP_USER` | `tu@gmail.com` | `tu@brevo.com` | Tu email |
| `SMTP_PASSWORD` | *App Password* | *API Password* | *Token/Password* |
| `SMTP_FROM_EMAIL` | `tu@gmail.com` | `noreply@tudominio.com` | Tu email |
| `IMAP_HOST` | `imap.gmail.com` | `imap.gmail.com` | Según provider |
| `IMAP_PORT` | `993` | `993` | Según provider |
| `IMAP_USER` | `tu@gmail.com` | `tu@gmail.com` | Tu email |
| `IMAP_PASSWORD` | *App Password* | *App Password* | *Token/Password* |

**Gmail - Generar App Password:**
```bash
1. https://myaccount.google.com/
2. Security → App passwords
3. Seleccionar: Mail, Windows Computer
4. Copiar contraseña (16 caracteres)
5. Usar como SMTP_PASSWORD e IMAP_PASSWORD
```

---

## 3️⃣ URLs y DOMINIOS

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `DOMAIN` | `api.reservas.example.com` | **Sin https://** - Dominio raíz |
| `BASE_URL` | `https://api.reservas.example.com` | **Con https://** - URL completa |
| `ENVIRONMENT` | `production` | Valores: `development`, `staging`, `production` |
| `ALLOWED_ORIGINS` | `https://admin.reservas.example.com,https://reservas.example.com` | CORS separado por comas |

**Ejemplo completo:**
```env
DOMAIN=reservas.tudominio.com
BASE_URL=https://reservas.tudominio.com
ENVIRONMENT=production
ALLOWED_ORIGINS=https://admin.tudominio.com,https://reservas.tudominio.com
```

---

## 4️⃣ BASE DE DATOS

### PostgreSQL

| Variable | Valor | Ejemplo | Notas |
|----------|-------|---------|-------|
| `DATABASE_URL` | URL completa | `postgresql+asyncpg://user:pass@host:5432/db` | **Async required** |
| `POSTGRES_USER` | Username | `alojamientos` | Usuario de BD |
| `POSTGRES_PASSWORD` | Password | `*generar_arriba*` | 🔒 **CRÍTICA** |
| `POSTGRES_DB` | Database name | `alojamientos_db` | Nombre de la BD |
| `DB_POOL_SIZE` | Número | `50` | Conexiones simultáneas |
| `DB_MAX_OVERFLOW` | Número | `25` | Conexiones exceso |

**Formato DATABASE_URL:**
```
postgresql+asyncpg://alojamientos:PASSWORD@postgres:5432/alojamientos_db
```

**Desglose:**
- `postgresql+asyncpg://` → Driver async (OBLIGATORIO)
- `alojamientos` → Usuario
- `:PASSWORD` → Contraseña (generar con openssl)
- `@postgres` → Host (en Docker, nombre del servicio)
- `:5432` → Puerto PostgreSQL
- `/alojamientos_db` → Nombre de base de datos

**Validación:**
```bash
psql postgresql://alojamientos:PASSWORD@host:5432/alojamientos_db -c "SELECT 1"
```

---

## 5️⃣ CACHE y LOCKS

### Redis

| Variable | Valor | Ejemplo | Notas |
|----------|-------|---------|-------|
| `REDIS_URL` | URL completa | `redis://:password@redis:6379/0` | **Con contraseña** |
| `REDIS_PASSWORD` | Password | `*generar_arriba*` | 🔒 **CRÍTICA** |

**Formato REDIS_URL:**
```
redis://:PASSWORD@redis:6379/0
```

**Desglose:**
- `redis://` → Protocolo
- `:PASSWORD@` → Contraseña (incluir `:` antes, incluso si vacía)
- `redis` → Host (en Docker, nombre del servicio)
- `:6379` → Puerto Redis
- `/0` → Base de datos (0-15, usar 0 por defecto)

**Validación:**
```bash
redis-cli -h redis -p 6379 -a PASSWORD ping
# Debe responder: PONG
```

---

## 6️⃣ EMAIL y SMTP

### Configuración Completa

```env
# === EMAIL OUTBOUND (SMTP) ===
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=reservas@tudominio.com
SMTP_PASSWORD=app_password_aqui    # App password de Gmail
SMTP_FROM_EMAIL=reservas@tudominio.com
SMTP_FROM_NAME="Sistema de Reservas"

# === EMAIL INBOUND (IMAP) ===
IMAP_ENABLED=true
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=reservas@tudominio.com
IMAP_PASSWORD=app_password_aqui    # Mismo app password
IMAP_POLL_INTERVAL_SECONDS=300     # Cada 5 minutos

# === EMAIL TEMPLATES ===
ADMIN_EMAIL=admin@tudominio.com
```

### Validación SMTP

```bash
# Test connection
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('tu@gmail.com', 'app_password')
print('✅ SMTP OK')
server.quit()
"
```

### Validación IMAP

```bash
# Test connection
python3 -c "
import imaplib
imap = imaplib.IMAP4_SSL('imap.gmail.com', 993)
imap.login('tu@gmail.com', 'app_password')
print('✅ IMAP OK')
imap.close()
"
```

---

## 7️⃣ SEGURIDAD

### JWT (JSON Web Tokens)

| Variable | Valor | Ejemplo | Notas |
|----------|-------|---------|-------|
| `JWT_SECRET` | Secret | `*generar_arriba*` | 🔒 **CRÍTICA** |
| `JWT_ALGORITHM` | Algoritmo | `HS256` | No cambiar |
| `JWT_EXPIRATION_HOURS` | Horas | `24` | Expiración de token |

### Admin Dashboard

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `ADMIN_ALLOWED_EMAILS` | CSV | `admin@tudominio.com,ops@tudominio.com` |
| `ADMIN_USERNAME` | Username | `admin` |
| `ADMIN_PASSWORD` | Hash | *Generado en primer login* |

### Rate Limiting

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `RATE_LIMIT_REQUESTS` | Número | `100` (requests por ventana) |
| `RATE_LIMIT_WINDOW_SECONDS` | Segundos | `60` |
| `RATE_LIMIT_ENABLED` | Boolean | `true` |

---

## 8️⃣ ARCHIVO .env COMPLETO TEMPLATE

**Copiar y rellenar:**

```bash
# ============================================
# AMBIENTE
# ============================================
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql+asyncpg://alojamientos:POSTGRES_PASSWORD@postgres:5432/alojamientos_db
POSTGRES_USER=alojamientos
POSTGRES_PASSWORD=GENERADO_ARRIBA
POSTGRES_DB=alojamientos_db
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=25

# ============================================
# REDIS (LOCKS)
# ============================================
REDIS_URL=redis://:REDIS_PASSWORD@redis:6379/0
REDIS_PASSWORD=GENERADO_ARRIBA

# ============================================
# WHATSAPP BUSINESS CLOUD API
# ============================================
WHATSAPP_PHONE_ID=OBTENER_DE_META
WHATSAPP_BUSINESS_ACCOUNT_ID=OBTENER_DE_META
WHATSAPP_ACCESS_TOKEN=OBTENER_DE_META
WHATSAPP_APP_SECRET=OBTENER_DE_META
WHATSAPP_VERIFY_TOKEN=GENERADO_ARRIBA

# ============================================
# MERCADO PAGO
# ============================================
MERCADOPAGO_ACCESS_TOKEN=OBTENER_DE_MP
MERCADOPAGO_PUBLIC_KEY=OBTENER_DE_MP
MERCADOPAGO_WEBHOOK_SECRET=GENERADO_ARRIBA

# ============================================
# EMAIL (SMTP/IMAP)
# ============================================
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=reservas@tudominio.com
SMTP_PASSWORD=OBTENER_GMAIL_APP_PASSWORD
SMTP_FROM_EMAIL=reservas@tudominio.com
SMTP_FROM_NAME=Sistema de Reservas
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=reservas@tudominio.com
IMAP_PASSWORD=OBTENER_GMAIL_APP_PASSWORD

# ============================================
# DOMAIN & URLS
# ============================================
DOMAIN=api.reservas.tudominio.com
BASE_URL=https://api.reservas.tudominio.com
ALLOWED_ORIGINS=https://admin.reservas.tudominio.com,https://reservas.tudominio.com

# ============================================
# SEGURIDAD
# ============================================
JWT_SECRET=GENERADO_ARRIBA
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_EXPIRATION_MINUTES=10080
ICS_SALT=GENERADO_ARRIBA

# ============================================
# ADMIN
# ============================================
ADMIN_ALLOWED_EMAILS=admin@tudominio.com
ADMIN_USERNAME=admin

# ============================================
# RATE LIMITING
# ============================================
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_ENABLED=true

# ============================================
# AUDIO/NLU
# ============================================
AUDIO_MODEL=base
AUDIO_MIN_CONFIDENCE=0.6

# ============================================
# JOBS
# ============================================
JOB_EXPIRATION_INTERVAL_SECONDS=300
ICAL_SYNC_INTERVAL_SECONDS=300

# ============================================
# OBSERVABILIDAD
# ============================================
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=GENERADO_ARRIBA
```

---

## ✅ CHECKLIST DE OBTENCIÓN

### Orden de Tareas (Antes de Deploy)

- [ ] **Paso 1: Generar secretos internos**
  - [ ] Generar `JWT_SECRET`
  - [ ] Generar `ICS_SALT`
  - [ ] Generar `POSTGRES_PASSWORD`
  - [ ] Generar `REDIS_PASSWORD`
  - [ ] Generar `WHATSAPP_VERIFY_TOKEN`
  - [ ] Generar `MERCADOPAGO_WEBHOOK_SECRET`
  - [ ] Generar `GRAFANA_ADMIN_PASSWORD`

- [ ] **Paso 2: Obtener credenciales WhatsApp**
  - [ ] Meta Business Account creada
  - [ ] App WhatsApp creada
  - [ ] `WHATSAPP_ACCESS_TOKEN` copiado
  - [ ] `WHATSAPP_APP_SECRET` copiado
  - [ ] `WHATSAPP_PHONE_ID` copiado
  - [ ] `WHATSAPP_BUSINESS_ACCOUNT_ID` copiado
  - [ ] Token validado con curl

- [ ] **Paso 3: Obtener credenciales Mercado Pago**
  - [ ] Cuenta MP creada
  - [ ] Aplicación MP creada
  - [ ] `MERCADOPAGO_ACCESS_TOKEN` copiado (PRODUCCIÓN, no Sandbox)
  - [ ] `MERCADOPAGO_PUBLIC_KEY` copiado
  - [ ] Token validado con curl

- [ ] **Paso 4: Configurar Email**
  - [ ] Gmail account creado (o proveedor elegido)
  - [ ] 2FA activado en Gmail
  - [ ] App Password generado
  - [ ] `SMTP_PASSWORD` / `IMAP_PASSWORD` copiados
  - [ ] SMTP validado con Python
  - [ ] IMAP validado con Python

- [ ] **Paso 5: Configurar Dominio**
  - [ ] Dominio registrado
  - [ ] DNS apuntando a servidor
  - [ ] `DOMAIN` confirmado
  - [ ] `BASE_URL` confirmado
  - [ ] ALLOWED_ORIGINS definido

- [ ] **Paso 6: Llenar .env**
  - [ ] Crear `.env` desde template
  - [ ] Todos los valores generados pegados
  - [ ] Todos los valores de terceros pegados
  - [ ] Validar sin líneas vacías
  - [ ] NO commitear a git

- [ ] **Paso 7: Pre-deploy validation**
  - [ ] `make test` pasa ✅
  - [ ] `docker-compose up` inicia sin errores ✅
  - [ ] `curl https://domain/api/v1/healthz` responde ✅
  - [ ] Webhooks configurados en Meta y MP ✅

---

## 🚨 SEGURIDAD: LISTA DE VERIFICACIÓN

| Aspecto | ✅ Acción |
|---------|----------|
| **Secretos** | ❌ NO commitear `.env` a git |
| **Secrets** | ✅ Usar GitHub Secrets para CI/CD |
| **Backups** | ✅ Guardar `.env` en lugar seguro (1Password, Vault, etc) |
| **Rotación** | ✅ Cambiar JWT_SECRET cada 90 días |
| **HTTPS** | ✅ Let's Encrypt configurado en nginx |
| **Logs** | ❌ NO loguear credenciales |
| **Access** | ✅ Limitar acceso a servidor a IPs conocidas |

---

## 📞 REFERENCIAS RÁPIDAS

**Obtener Access Token WhatsApp:**
```bash
curl -X GET "https://graph.instagram.com/me/whatsapp_business_accounts?access_token=YOUR_TOKEN"
```

**Obtener Info MP Account:**
```bash
curl -X GET "https://api.mercadopago.com/v1/payments?access_token=APP_USR-..."
```

**Test Email SMTP:**
```bash
python3 -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('Test')
msg['Subject'] = 'Test'
msg['From'] = 'tu@gmail.com'
msg['To'] = 'tu@gmail.com'
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('tu@gmail.com', 'app_password')
server.send_message(msg)
server.quit()
print('✅ Email enviado')
"
```

**Health Check:**
```bash
curl -X GET "https://api.reservas.tudominio.com/api/v1/healthz"
```

---

**Generado:** 16 de Octubre, 2025
**Estado:** PRODUCCIÓN-LISTO
**Próximo paso:** Rellenar .env y hacer deploy
