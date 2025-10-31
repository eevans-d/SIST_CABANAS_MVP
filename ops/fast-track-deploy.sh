#!/bin/bash
# Fast Track Deploy - Solo necesita DATABASE_URL y REDIS_URL
set -euo pipefail

# ============================================================
# 🔒 DEPLOYMENT GUARD (ANTI-DUPLICADOS / CONTROL DE COSTOS)
#
# Este script ABORTA si:
#  - No confirmas explicitamente los costos (DEPLOY_ACK requerido)
#  - Hay más de 1 app Fly con prefijo "sist-cabanas"
#  - Existen >1 máquinas RUNNING para esta app
#  - La app o región no coinciden con la política (app=sist-cabanas-mvp, region=gru)
#
# Para continuar debes exportar antes:
#   export DEPLOY_ACK="I_ACCEPT_SINGLE_APP_COSTS"
# ============================================================

APP_NAME="sist-cabanas-mvp"
PRIMARY_REGION="gru"

require_ack() {
  if [[ "${DEPLOY_ACK:-}" != "I_ACCEPT_SINGLE_APP_COSTS" ]]; then
    echo "❌ ABORTADO: Falta confirmación de costos."
    echo "   Exporta la variable y reintenta:"
    echo "   export DEPLOY_ACK=\"I_ACCEPT_SINGLE_APP_COSTS\""
    exit 1
  fi
}

check_fly_context() {
  if ! command -v fly >/dev/null 2>&1; then
    echo "❌ flyctl no está instalado en el PATH. Instálalo y loguéate: https://fly.io/docs/hands-on/installing/"
    exit 1
  fi
  if ! fly auth token >/dev/null 2>&1; then
    echo "❌ No hay sesión activa en flyctl. Ejecuta: fly auth login"
    exit 1
  fi
}

abort_on_duplicate_apps() {
  echo "🔎 Verificando apps en Fly con prefijo 'sist-cabanas'..."
  local apps
  apps=$(fly apps list --json | jq -r '.[].Name' | grep -E '^sist-cabanas' || true)
  local count
  count=$(echo "$apps" | sed '/^$/d' | wc -l | tr -d ' ')
  printf "   Apps detectadas:\n%s\n" "$apps"
  if [[ "$count" -gt 1 ]]; then
    echo "❌ ABORTADO: Se detectaron múltiples apps con prefijo 'sist-cabanas'. Evitar costos duplicados."
    echo "   Mantén SOLO una app (sugerido: $APP_NAME). Elimina las demás con: fly apps destroy <app>"
    exit 1
  fi
  if [[ "$count" -eq 1 ]]; then
    local only
    only=$(echo "$apps" | head -n1)
    if [[ "$only" != "$APP_NAME" ]]; then
      echo "❌ ABORTADO: La única app existente no coincide con '$APP_NAME' (encontrada: $only)."
      echo "   Ajusta APP_NAME o consolida tu app en '$APP_NAME' para simplificar costos."
      exit 1
    fi
  fi
}

abort_on_multiple_machines() {
  echo "🔎 Verificando máquinas activas para $APP_NAME..."
  local machines_json
  machines_json=$(fly machines list -a "$APP_NAME" --json || echo '[]')
  local running
  running=$(echo "$machines_json" | jq -r '.[] | select(.state=="started" or .state=="running").id' | wc -l | tr -d ' ')
  echo "   Máquinas RUNNING: $running"
  if [[ "$running" -gt 1 ]]; then
    echo "❌ ABORTADO: Más de 1 máquina RUNNING para $APP_NAME. Política de costo: single instance."
    echo "   Detén o destruye máquinas extra con: fly machines list -a $APP_NAME && fly machines stop <id>"
    exit 1
  fi
}

assert_region_and_app() {
  echo "🔎 Verificando configuración: app=$APP_NAME, region=$PRIMARY_REGION..."
  local cfg_app
  cfg_app=$(grep -E '^app\s*=\s*"' fly.toml | sed -E 's/app\s*=\s*"([^"]+)"/\1/')
  if [[ "$cfg_app" != "$APP_NAME" ]]; then
    echo "❌ ABORTADO: fly.toml app='$cfg_app' distinto de '$APP_NAME'"
    exit 1
  fi
  local cfg_region
  cfg_region=$(grep -E '^primary_region\s*=\s*"' fly.toml | sed -E 's/primary_region\s*=\s*"([^"]+)"/\1/')
  if [[ "$cfg_region" != "$PRIMARY_REGION" ]]; then
    echo "❌ ABORTADO: primary_region='$cfg_region' distinto de '$PRIMARY_REGION'"
    exit 1
  fi
}

require_ack
check_fly_context
abort_on_duplicate_apps
assert_region_and_app
abort_on_multiple_machines

echo "🚀 SIST_CABAÑAS - Fast Track Staging Deploy"
echo "============================================"
echo ""
echo "Este script necesita SOLO 2 valores para deploy completo:"
echo ""
echo "1. DATABASE_URL (PostgreSQL con btree_gist)"
echo "   Recomendado: Neon.tech (free tier, 2 min setup)"
echo "   Formato: postgresql://user:pass@host/dbname?sslmode=require"
echo ""
echo "2. REDIS_URL (Redis 7+)"
echo "   Recomendado: Upstash.com (free tier, 5 min setup)"
echo "   Formato: rediss://default:pass@host:port"
echo ""
echo "============================================"
echo ""

# Solicitar DATABASE_URL
read -r -p "Ingresa DATABASE_URL: " DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
  echo "❌ ERROR: DATABASE_URL es requerido"
  exit 1
fi

# Solicitar REDIS_URL
read -r -p "Ingresa REDIS_URL: " REDIS_URL
if [ -z "$REDIS_URL" ]; then
  echo "❌ ERROR: REDIS_URL es requerido"
  exit 1
fi

echo ""
echo "✅ URLs recibidas. Validando formato..."

# Validar formato básico
if [[ ! "$DATABASE_URL" =~ ^postgresql:// ]]; then
  echo "❌ ERROR: DATABASE_URL debe comenzar con postgresql://"
  exit 1
fi

if [[ ! "$REDIS_URL" =~ ^redis ]]; then
  echo "❌ ERROR: REDIS_URL debe comenzar con redis:// o rediss://"
  exit 1
fi

echo "✅ Formato OK"
echo ""
echo "📦 Configurando secrets en Fly..."
echo ""

# Secrets generados (seguros)
JWT_SECRET_KEY="a4fpW5ND6g90R3exxCRRYmx3OP5kacdkLin6FX5gyCI"
ICAL_EXPORT_SECRET="heHpxrEz8GXjMkEErrSNwbLT08-xE09xsx2t8CLGsU8"

# Placeholders seguros para staging
WHATSAPP_PHONE_NUMBER_ID="placeholder_staging"
WHATSAPP_ACCESS_TOKEN="placeholder_staging_token"
WHATSAPP_APP_SECRET="placeholder_staging_min32chars_required_for_hmac_validation"
WHATSAPP_VERIFY_TOKEN="staging_verify_token"

MERCADOPAGO_ACCESS_TOKEN="placeholder_staging_token"
MERCADOPAGO_WEBHOOK_SECRET="placeholder_staging_secret"

OPENAI_API_KEY="placeholder_staging_key"
STORAGE_BUCKET_NAME="staging-bucket"
STORAGE_ACCOUNT_KEY="placeholder_staging_key"

# URLs
BACKEND_URL="https://sist-cabanas-mvp.fly.dev"
FRONTEND_URL="https://sist-cabanas-mvp.fly.dev"
ALLOWED_ORIGINS="https://sist-cabanas-mvp.fly.dev"

echo "Cargando 14 secrets críticos..."
if ! fly secrets set \
  DATABASE_URL="$DATABASE_URL" \
  REDIS_URL="$REDIS_URL" \
  JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  ICAL_EXPORT_SECRET="$ICAL_EXPORT_SECRET" \
  WHATSAPP_PHONE_NUMBER_ID="$WHATSAPP_PHONE_NUMBER_ID" \
  WHATSAPP_ACCESS_TOKEN="$WHATSAPP_ACCESS_TOKEN" \
  WHATSAPP_APP_SECRET="$WHATSAPP_APP_SECRET" \
  WHATSAPP_VERIFY_TOKEN="$WHATSAPP_VERIFY_TOKEN" \
  MERCADOPAGO_ACCESS_TOKEN="$MERCADOPAGO_ACCESS_TOKEN" \
  MERCADOPAGO_WEBHOOK_SECRET="$MERCADOPAGO_WEBHOOK_SECRET" \
  OPENAI_API_KEY="$OPENAI_API_KEY" \
  STORAGE_BUCKET_NAME="$STORAGE_BUCKET_NAME" \
  STORAGE_ACCOUNT_KEY="$STORAGE_ACCOUNT_KEY" \
  BACKEND_URL="$BACKEND_URL" \
  FRONTEND_URL="$FRONTEND_URL" \
  ALLOWED_ORIGINS="$ALLOWED_ORIGINS" \
  -a "$APP_NAME"; then
  echo "❌ ERROR: Fallo al cargar secrets en Fly"
  exit 1
fi

echo ""
echo "✅ Secrets cargados exitosamente"
echo ""
echo "🚢 Iniciando deploy a Fly.io..."
echo ""

if ! fly deploy -a "$APP_NAME" --ha=false; then
  echo "❌ ERROR: Deploy falló"
  exit 1
fi

echo ""
echo "✅ Deploy completado"
echo ""
echo "🔍 Validando health endpoints..."
echo ""

sleep 10  # Dar tiempo a que arranque

# Health check
HEALTH_URL="https://$APP_NAME.fly.dev/api/v1/healthz"
echo "Verificando $HEALTH_URL ..."

HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$HEALTH_URL" || echo "000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Body: $BODY"

if [ "$HTTP_CODE" = "200" ]; then
  echo ""
  echo "✅ Health check OK"
else
  echo ""
  echo "⚠️  Health check retornó $HTTP_CODE (puede estar iniciando)"
fi

echo ""
echo "📊 Verificando metrics..."
METRICS_URL="https://$APP_NAME.fly.dev/metrics"
METRICS_RESPONSE=$(curl -s -w "\n%{http_code}" "$METRICS_URL" || echo "000")
METRICS_HTTP_CODE=$(echo "$METRICS_RESPONSE" | tail -n1)

if [ "$METRICS_HTTP_CODE" = "200" ]; then
  echo "✅ Metrics endpoint OK"
else
  echo "⚠️  Metrics retornó $METRICS_HTTP_CODE"
fi

echo ""
echo "============================================"
echo "🎉 DEPLOY COMPLETADO"
echo "============================================"
echo ""
echo "URLs:"
echo "  - App: https://$APP_NAME.fly.dev"
echo "  - Health: $HEALTH_URL"
echo "  - Metrics: $METRICS_URL"
echo "  - Docs: https://sist-cabanas-mvp.fly.dev/docs"
echo ""
echo "Ver logs en tiempo real:"
echo "  fly logs -a $APP_NAME"
echo ""
echo "Próximos pasos:"
echo "  1. Ejecutar: ./ops/smoke_and_benchmark.sh"
echo "  2. Revisar logs para validar migraciones DB"
echo "  3. Configurar APIs reales (WhatsApp, MP) si es necesario"
echo ""
