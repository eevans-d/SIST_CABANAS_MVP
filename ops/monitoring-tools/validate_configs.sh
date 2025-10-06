#!/usr/bin/env bash
set -euo pipefail

# validate_configs.sh - Valida configs de Prometheus, Alertmanager y dashboards JSON

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

PROM_CONFIG="monitoring/prometheus/prometheus.yml"
PROM_RULES="monitoring/prometheus/rules/alerts.yml"
AM_CONFIG="monitoring/alertmanager/alertmanager.yml"

# Validar Prometheus
if command -v promtool >/dev/null 2>&1; then
  echo "[INFO] Validando Prometheus config y reglas..."
  promtool check config "$PROM_CONFIG"
  promtool check rules "$PROM_RULES"
else
  echo "[WARN] promtool no encontrado, omitiendo validación de Prometheus"
fi

# Validar Alertmanager
if command -v amtool >/dev/null 2>&1; then
  echo "[INFO] Validando Alertmanager config..."
  amtool check-config "$AM_CONFIG"
else
  echo "[WARN] amtool no encontrado, omitiendo validación de Alertmanager"
fi

# Validar JSON dashboards
for f in monitoring/grafana/dashboards/*.json; do
  if command -v jq >/dev/null 2>&1; then
    jq empty "$f"
  else
    echo "[WARN] jq no encontrado, omitiendo validación de $f"
  fi
done

echo "[OK] Validaciones completadas"
