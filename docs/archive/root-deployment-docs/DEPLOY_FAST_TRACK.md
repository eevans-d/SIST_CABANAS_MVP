# 🚀 Fast Track Deployment - Staging

> ⚠️ Cost Guard (Anti-duplicados) — Obligatorio antes de desplegar
>
> 1) Exportar confirmación explícita de costos:
>
>    export DEPLOY_ACK="I_ACCEPT_SINGLE_APP_COSTS"
>
> 2) Ejecutar chequeo de seguridad:
>
>    ./ops/deploy-check.sh
>
> El despliegue se ABORTA si hay apps duplicadas, múltiples máquinas RUNNING,
> app/region distintas (app=sist-cabanas-mvp, region=gru) o falta DEPLOY_ACK.

**Fecha:** 31 de octubre 2025
**Objetivo:** Deploy staging en <30 minutos

---

## ✅ Secrets Generados (Seguros)

```bash
# Ya generados - USAR ESTOS:
JWT_SECRET_KEY="a4fpW5ND6g90R3exxCRRYmx3OP5kacdkLin6FX5gyCI"
ICAL_EXPORT_SECRET="heHpxrEz8GXjMkEErrSNwbLT08-xE09xsx2t8CLGsU8"
```

---

## 🗄️ Base de Datos: Opción Rápida

**Recomendado:** [Neon](https://neon.tech) (PostgreSQL serverless, free tier, setup 2 min)

### Pasos Neon:
1. Ir a https://neon.tech
2. Crear cuenta → New Project
3. Nombre: `sist-cabanas-staging`
4. Region: `AWS South America (São Paulo)` o `US East`
5. Copiar `DATABASE_URL` (formato: `postgresql://user:pass@host/dbname?sslmode=require`)

**Alternativa:** [Supabase](https://supabase.com) - similar, también free tier.

---

## 🔴 Redis: Upstash (Instantáneo)

### Pasos Upstash:
1. Ir a https://upstash.com
2. Crear cuenta → Create Database
3. Nombre: `sist-cabanas-staging`
4. Region: `South America (São Paulo)` o closest
5. Copiar `REDIS_URL` (formato: `rediss://default:pass@host:port`)

---

## 📋 Checklist Secrets Mínimos para Deploy

```bash
# 1. CRÍTICOS (sin estos NO arranca):
DATABASE_URL="postgresql://..."           # ← DE NEON
REDIS_URL="rediss://..."                  # ← DE UPSTASH
JWT_SECRET_KEY="a4fpW5ND6g90R3e..."       # ✅ YA GENERADO
ICAL_EXPORT_SECRET="heHpxrEz8GXj..."     # ✅ YA GENERADO

# 2. PLACEHOLDERS (para que NO crashee):
WHATSAPP_PHONE_NUMBER_ID="placeholder_staging"
WHATSAPP_ACCESS_TOKEN="placeholder_staging"
WHATSAPP_APP_SECRET="placeholder_staging_min32chars_required"
WHATSAPP_VERIFY_TOKEN="staging_verify_token"

MERCADOPAGO_ACCESS_TOKEN="placeholder_staging"
MERCADOPAGO_WEBHOOK_SECRET="placeholder_staging"

OPENAI_API_KEY="placeholder_staging"
STORAGE_BUCKET_NAME="staging-bucket"
STORAGE_ACCOUNT_KEY="placeholder_staging"

# 3. URLS (default OK para staging):
BACKEND_URL="https://sist-cabanas-mvp.fly.dev"
FRONTEND_URL="https://sist-cabanas-mvp.fly.dev"
ALLOWED_ORIGINS="https://sist-cabanas-mvp.fly.dev"
```

---

## ⚡ Comandos para Deploy Inmediato

Una vez tengas `DATABASE_URL` y `REDIS_URL`:

```bash
# 0. Guardas de costo (obligatorio)
export DEPLOY_ACK="I_ACCEPT_SINGLE_APP_COSTS"
./ops/deploy-check.sh  # debe retornar: CHECKS OK

# 1. Cargar secrets en Fly
fly secrets set \
  DATABASE_URL="postgresql://..." \
  REDIS_URL="rediss://..." \
  JWT_SECRET_KEY="a4fpW5ND6g90R3exxCRRYmx3OP5kacdkLin6FX5gyCI" \
  ICAL_EXPORT_SECRET="heHpxrEz8GXjMkEErrSNwbLT08-xE09xsx2t8CLGsU8" \
  WHATSAPP_PHONE_NUMBER_ID="placeholder_staging" \
  WHATSAPP_ACCESS_TOKEN="placeholder_staging" \
  WHATSAPP_APP_SECRET="placeholder_staging_min32chars" \
  WHATSAPP_VERIFY_TOKEN="staging_verify_token" \
  MERCADOPAGO_ACCESS_TOKEN="placeholder_staging" \
  MERCADOPAGO_WEBHOOK_SECRET="placeholder_staging" \
  OPENAI_API_KEY="placeholder_staging" \
  STORAGE_BUCKET_NAME="staging-bucket" \
  STORAGE_ACCOUNT_KEY="placeholder_staging" \
  BACKEND_URL="https://sist-cabanas-mvp.fly.dev" \
  FRONTEND_URL="https://sist-cabanas-mvp.fly.dev" \
  ALLOWED_ORIGINS="https://sist-cabanas-mvp.fly.dev" \
  -a sist-cabanas-mvp

# 2. Deploy (single instance)
fly deploy -a sist-cabanas-mvp --ha=false

# 3. Validar health
curl https://sist-cabanas-mvp.fly.dev/api/v1/healthz

# 4. Ver logs
fly logs -a sist-cabanas-mvp
```

---

## 🎯 Estado Actual

- [x] Secrets JWT/ICS generados
- [ ] DATABASE_URL de Neon/Supabase (BLOCKER)
- [ ] REDIS_URL de Upstash (5 min)
- [ ] fly secrets set (1 min)
- [ ] fly deploy (5 min)
- [ ] smoke test (2 min)

**SIGUIENTE PASO:** Crear base de datos en Neon (2 minutos) y proveer DATABASE_URL.
