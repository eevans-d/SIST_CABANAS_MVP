#!/usr/bin/env bash
set -euo pipefail

# test_alert_slack.sh - Envía una alerta de prueba a Slack a través de Alertmanager (si está configurado)

ALERTMANAGER_URL=${ALERTMANAGER_URL:-"http://localhost:9093"}

read -r -d '' PAYLOAD <<'JSON'
{
  "receiver": "slack-default",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "TestAlert",
        "severity": "info"
      },
      "annotations": {
        "summary": "Test alert from script",
        "description": "This is a test alert sent at $(date -u +%FT%TZ)"
      },
      "startsAt": "$(date -u +%FT%TZ)",
      "endsAt": "$(date -u -d '+5 minutes' +%FT%TZ)",
      "generatorURL": "script://local/test"
    }
  ]
}
JSON

# Reemplazar las variables de fecha embebidas
eval "echo \"$PAYLOAD\"" | curl -sS -XPOST -H 'Content-Type: application/json' --data-binary @- "$ALERTMANAGER_URL/api/v1/alerts"

echo "[OK] Alerta de prueba enviada a Alertmanager (${ALERTMANAGER_URL})"
