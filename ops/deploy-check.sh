#!/bin/bash
# Deployment Safety Check - evita despliegues duplicados y costos innecesarios
set -euo pipefail

APP_NAME="sist-cabanas-mvp"
PRIMARY_REGION="gru"

if ! command -v fly >/dev/null 2>&1; then
  echo "❌ flyctl no instalado. https://fly.io/docs/hands-on/installing/"
  exit 1
fi
if ! fly auth token >/dev/null 2>&1; then
  echo "❌ No hay sesión en flyctl. Ejecuta: fly auth login"
  exit 1
fi

status=0

echo "🔎 [1/4] Verificando apps con prefijo 'sist-cabanas'..."
apps=$(fly apps list --json | jq -r '.[].Name' | grep -E '^sist-cabanas' || true)
count=$(echo "$apps" | sed '/^$/d' | wc -l | tr -d ' ')
printf "    Apps:\n%s\n" "$apps"
if [[ "$count" -gt 1 ]]; then
  echo "❌ Encontradas múltiples apps. Mantén SOLO una: $APP_NAME"
  status=1
fi
if [[ "$count" -eq 1 ]]; then
  only=$(echo "$apps" | head -n1)
  if [[ "$only" != "$APP_NAME" ]]; then
    echo "❌ App única no coincide con '$APP_NAME' (encontrada: $only)"
    status=1
  fi
fi

echo "🔎 [2/4] Verificando máquinas RUNNING..."
machines_json=$(fly machines list -a "$APP_NAME" --json || echo '[]')
running=$(echo "$machines_json" | jq -r '.[] | select(.state=="started" or .state=="running").id' | wc -l | tr -d ' ')
echo "    RUNNING: $running"
if [[ "$running" -gt 1 ]]; then
  echo "❌ Más de 1 máquina RUNNING. Política: single instance."
  status=1
fi

echo "🔎 [3/4] Verificando fly.toml (app/region)..."
cfg_app=$(awk -F '"' '/^app[[:space:]]*=/{print $2; exit}' fly.toml)
if [[ "$cfg_app" != "$APP_NAME" ]]; then
  echo "❌ fly.toml app='$cfg_app' distinto de '$APP_NAME'"
  status=1
fi
cfg_region=$(awk -F '"' '/^primary_region[[:space:]]*=/{print $2; exit}' fly.toml)
if [[ "$cfg_region" != "$PRIMARY_REGION" ]]; then
  echo "❌ primary_region='$cfg_region' distinto de '$PRIMARY_REGION'"
  status=1
fi

echo "🔎 [4/4] Confirmación de costos (DEPLOY_ACK)..."
if [[ "${DEPLOY_ACK:-}" != "I_ACCEPT_SINGLE_APP_COSTS" ]]; then
  echo "❌ Falta DEPLOY_ACK=I_ACCEPT_SINGLE_APP_COSTS"
  status=1
fi

if [[ "$status" -eq 0 ]]; then
  echo "✅ CHECKS OK - Seguro para desplegar"
else
  echo "❌ CHECKS FALLIDOS - Corrige antes de desplegar"
fi
exit "$status"
