#!/usr/bin/env bash
set -euo pipefail

# Carga secretos de Fly.io desde un archivo env y los aplica a la app indicada
# Uso:
#   ./ops/set_fly_secrets.sh <app-name> env/.env.fly.staging

APP_NAME=${1:-}
ENV_FILE=${2:-}

if ! command -v flyctl >/dev/null 2>&1; then
  echo "Error: flyctl no está instalado. Ver: https://fly.io/docs/hands-on/install/" >&2
  exit 1
fi

if [[ -z "$APP_NAME" || -z "$ENV_FILE" ]]; then
  echo "Uso: $0 <app-name> <env-file>" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: archivo $ENV_FILE no existe" >&2
  exit 1
fi

# Cargar variables del archivo
set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

# Validar mínimos
REQUIRED=(DATABASE_URL REDIS_URL JWT_SECRET ADMIN_ALLOWED_EMAILS)
for k in "${REQUIRED[@]}"; do
  if [[ -z "${!k:-}" ]]; then
    echo "Error: falta definir $k en $ENV_FILE" >&2
    MISSING=1
  fi
done
if [[ "${MISSING:-0}" -eq 1 ]]; then
  exit 1
fi

# Preparar lista de claves a setear (solo si están definidas)
SECRETS=()
maybe_add() {
  local key=$1
  local val=${!key:-}
  if [[ -n "$val" ]]; then
    SECRETS+=("$key=$val")
  fi
}

maybe_add DATABASE_URL
maybe_add REDIS_URL
maybe_add JWT_SECRET
maybe_add WHATSAPP_ACCESS_TOKEN
maybe_add WHATSAPP_APP_SECRET
maybe_add WHATSAPP_PHONE_ID
maybe_add WHATSAPP_VERIFY_TOKEN
maybe_add MERCADOPAGO_ACCESS_TOKEN
maybe_add MERCADOPAGO_WEBHOOK_SECRET
maybe_add ADMIN_ALLOWED_EMAILS
maybe_add ALLOWED_ORIGINS
maybe_add ICS_SALT

# Parámetros operativos
maybe_add RATE_LIMIT_ENABLED
maybe_add RATE_LIMIT_REQUESTS
maybe_add RATE_LIMIT_WINDOW_SECONDS
maybe_add JOB_EXPIRATION_INTERVAL_SECONDS
maybe_add JOB_ICAL_INTERVAL_SECONDS

if [[ ${#SECRETS[@]} -eq 0 ]]; then
  echo "No hay secretos para setear" >&2
  exit 0
fi

# Aplicar secretos
printf '%s\n' "${SECRETS[@]}" | flyctl secrets set -a "$APP_NAME" --stdin

echo "✅ Secretos cargados en app: $APP_NAME"
