# 🎯 RESUMEN: Lo que Debes Obtener ANTES de Deploy

**Sistema MVP - 16 de Octubre de 2025**

---

## 📌 LISTA RÁPIDA (Copiar y Rellenar)

```
CRÍTICAS - GENERAR ESTOS (Comando Python/OpenSSL):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ JWT_SECRET               (48 chars, base64)
☐ ICS_SALT                 (32 chars, hex)
☐ POSTGRES_PASSWORD        (32 chars, base64)
☐ REDIS_PASSWORD           (32 chars, base64)
☐ WHATSAPP_VERIFY_TOKEN    (32 chars, hex)
☐ MERCADOPAGO_WEBHOOK_SECRET (32 chars, base64)
☐ GRAFANA_ADMIN_PASSWORD   (16 chars, base64)


CRÍTICAS - OBTENER DE TERCEROS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ WHATSAPP_ACCESS_TOKEN        (Meta Dev Console) → EAAB...
☐ WHATSAPP_APP_SECRET          (Meta Dev Console) → abc123...
☐ WHATSAPP_PHONE_ID            (Meta Dev Console) → 15551234567
☐ WHATSAPP_BUSINESS_ACCOUNT_ID (Meta Dev Console) → 12345678...
☐ MERCADOPAGO_ACCESS_TOKEN     (MP Dev Dashboard) → APP_USR-...
☐ MERCADOPAGO_PUBLIC_KEY       (MP Dev Dashboard) → APP_USR-...
☐ SMTP_PASSWORD                (Gmail App Password) → 16 chars
☐ IMAP_PASSWORD                (Gmail App Password) → 16 chars (igual a SMTP)


IMPORTANTES - CONFIGURAR:
━━━━━━━━━━━━━━━━━━━━━━━━━
☐ DOMAIN                  → api.reservas.tudominio.com
☐ BASE_URL                → https://api.reservas.tudominio.com
☐ ENVIRONMENT             → production
☐ ALLOWED_ORIGINS         → https://admin.tudominio.com,https://reservas.tudominio.com
☐ ADMIN_ALLOWED_EMAILS    → admin@tudominio.com
```

---

## ⏱️ TIEMPO POR TAREA

| Tarea | Tiempo | Complejidad |
|-------|--------|-------------|
| Generar Secretos | 5 min | ⭐ Muy fácil |
| Obtener WhatsApp | 30 min | ⭐⭐ Fácil |
| Obtener Mercado Pago | 20 min | ⭐⭐ Fácil |
| Configurar Email | 15 min | ⭐⭐ Fácil |
| Configurar Dominio | 10 min | ⭐⭐ Fácil |
| Llenar .env | 10 min | ⭐ Muy fácil |
| **TOTAL** | **90 min** | **Fácil** |

---

## 🔗 DÓNDE OBTENER CADA COSA

### Meta / WhatsApp
👉 https://developers.facebook.com/apps/
1. Login → Seleccionar app → WhatsApp
2. Settings → Copiar `WHATSAPP_APP_SECRET`
3. Getting Started → Copiar `WHATSAPP_ACCESS_TOKEN`
4. Phone Numbers → Copiar `WHATSAPP_PHONE_ID`
5. About → Copiar `WHATSAPP_BUSINESS_ACCOUNT_ID`

### Mercado Pago
👉 https://www.mercadopago.com.ar/developers/
1. Login → Mis aplicaciones → [Tu App]
2. Credenciales → **Tab PRODUCCIÓN** (no Sandbox)
3. Copiar `MERCADOPAGO_ACCESS_TOKEN` + `MERCADOPAGO_PUBLIC_KEY`

### Gmail (Email)
👉 https://myaccount.google.com/
1. Security → Activar 2-Step Verification
2. App passwords → Mail, Windows Computer
3. Copiar contraseña generada (usar para SMTP e IMAP)

### Dominio
👉 Usar proveedor que tengas (GoDaddy, Namecheap, etc)
1. Registrar o usar existente
2. Apuntar DNS a tu servidor
3. Confirmar que responde en navegador

---

## 🎛️ GENERADOR DE SECRETOS (Copiar y pegar en terminal)

```bash
# Ejecutar estos comandos en terminal para generar valores

echo "=== GENERANDO SECRETOS ==="

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
echo "✅ Guardar TODOS estos valores en 1Password o similar"
```

---

## ✅ TEMPLATE .env MÍNIMO

```bash
# CRÍTICOS - GENERAR
JWT_SECRET=<PEGAR_AQUI>
ICS_SALT=<PEGAR_AQUI>
POSTGRES_PASSWORD=<PEGAR_AQUI>
REDIS_PASSWORD=<PEGAR_AQUI>
WHATSAPP_VERIFY_TOKEN=<PEGAR_AQUI>
MERCADOPAGO_WEBHOOK_SECRET=<PEGAR_AQUI>

# CRÍTICOS - OBTENER
WHATSAPP_ACCESS_TOKEN=<META>
WHATSAPP_APP_SECRET=<META>
WHATSAPP_PHONE_ID=<META>
WHATSAPP_BUSINESS_ACCOUNT_ID=<META>
MERCADOPAGO_ACCESS_TOKEN=<MP>
MERCADOPAGO_PUBLIC_KEY=<MP>
SMTP_USER=tu@gmail.com
SMTP_PASSWORD=<GMAIL_APP_PASSWORD>
IMAP_USER=tu@gmail.com
IMAP_PASSWORD=<GMAIL_APP_PASSWORD>

# IMPORTANTES
DOMAIN=api.reservas.tudominio.com
BASE_URL=https://api.reservas.tudominio.com
ENVIRONMENT=production
ALLOWED_ORIGINS=https://admin.tudominio.com,https://reservas.tudominio.com
ADMIN_ALLOWED_EMAILS=admin@tudominio.com
SMTP_FROM_EMAIL=reservas@tudominio.com

# AUTO-GENERADAS
DATABASE_URL=postgresql+asyncpg://alojamientos:$POSTGRES_PASSWORD@postgres:5432/alojamientos_db
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0
```

---

## 🚨 REGLAS DE ORO

```
❌ NUNCA:
- Commitear .env a git
- Compartir credenciales por Slack/Email
- Usar Sandbox en producción
- Loguear credenciales

✅ SIEMPRE:
- Guardar .env en 1Password/LastPass
- Usar GitHub Secrets para CI/CD
- Validar todos los valores ANTES de deploy
- Usar HTTPS con Let's Encrypt
```

---

## 📋 ARCHIVOS DE REFERENCIA

En el repositorio tienes:

1. **`GUIA_CREDENCIALES_PRODUCCION.md`** (17 KB)
   - Guía completa y detallada
   - Scripts de validación
   - Instrucciones paso-a-paso

2. **`CREDENCIALES_RESUMEN_EJECUTIVO.md`** (7.7 KB)
   - Tabla rápida de valores
   - Resumen ejecutivo
   - Checklist simplificado

3. **`STATUS_FINAL_MVP.md`** (18 KB)
   - Estado del sistema
   - Validaciones completadas

4. **`.github/copilot-instructions.md`** (18 KB)
   - Instrucciones para agentes IA
   - Paterns implementados
   - Decisiones de arquitectura

---

## 🎬 PRÓXIMOS PASOS (Después de obtener credenciales)

```
1. Llenar .env completamente
2. $ make test                      → ✅ Debe pasar
3. $ docker-compose up             → ✅ Debe iniciar
4. $ curl https://domain/healthz   → ✅ Debe responder
5. Configurar webhooks en Meta + MP
6. Deploy a producción
```

---

**Tiempo total: ~2 horas**
**Complejidad: Fácil**
**Documentación: Completa y detallada**
