#!/usr/bin/env bash
set -euo pipefail

# Simple smoke test para entorno Docker Compose
# Requisitos: docker compose, curl, jq

RED="\e[31m"; GREEN="\e[32m"; YELLOW="\e[33m"; NC="\e[0m"

info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
ok() { echo -e "${GREEN}[OK]${NC} $*"; }
err() { echo -e "${RED}[ERR]${NC} $*"; }

info "Levantando stack..."
docker compose up -d --build

info "Esperando healthz..."
for i in {1..60}; do
  STATUS=$(curl -s http://localhost:80/api/v1/healthz | jq -r .status || true)
  if [[ "$STATUS" == "healthy" || "$STATUS" == "degraded" ]]; then
    ok "Healthz: $STATUS"
    break
  fi
  sleep 3
  if [[ $i -eq 60 ]]; then err "Timeout esperando healthz"; exit 1; fi
done

info "Probando métricas..."
curl -sf http://localhost:80/metrics > /dev/null && ok "Metrics OK" || { err "Metrics FAIL"; exit 1; }

info "Creando pre-reserva de smoke..."
ACC_ID=${ACC_ID:-1}
BODY=$(cat <<JSON
{
  "accommodation_id": $ACC_ID,
  "check_in": "$(date -d "+7 days" +%F)",
  "check_out": "$(date -d "+9 days" +%F)",
  "guests": 2,
  "channel": "whatsapp",
  "contact_name": "Smoke Test",
  "contact_phone": "+549111111"
}
JSON
)
RESP=$(curl -s -X POST http://localhost:80/api/v1/reservations/pre-reserve -H 'Content-Type: application/json' -d "$BODY")
CODE=$(echo "$RESP" | jq -r .code)
if [[ "$CODE" == "null" || -z "$CODE" ]]; then err "Pre-reserve FAIL: $RESP"; exit 1; fi
ok "Pre-reserve OK: $CODE"

ok "Smoke test completado"
