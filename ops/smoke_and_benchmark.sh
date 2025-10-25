#!/usr/bin/env bash
set -euo pipefail

# Ejecuta smoke checks y el benchmark de runtime contra una BASE_URL
# Uso:
#   ./ops/smoke_and_benchmark.sh https://<app>.fly.dev

BASE_URL=${1:-}
if [[ -z "$BASE_URL" ]]; then
  echo "Uso: $0 <BASE_URL> (ej: https://sist-cabanas-mvp.fly.dev)" >&2
  exit 1
fi

say() { printf "\n➡️  %s\n" "$*"; }

say "Smoke: /healthz"
curl -sS "$BASE_URL/api/v1/healthz" | python -m json.tool | sed -e 's/^/  /'

say "Smoke: /readyz"
curl -sS "$BASE_URL/api/v1/readyz" | python -m json.tool | sed -e 's/^/  /'

say "Smoke: /metrics (primeras 10 líneas)"
curl -sS "$BASE_URL/metrics" | head -n 10 | sed -e 's/^/  /'

say "Benchmark runtime (concurrency=10)"
PYTHONPATH=backend python backend/scripts/runtime_benchmark.py \
  --base-url "$BASE_URL" \
  --concurrency 10 \
  --requests 100

say "Listo. Revisa también backend/docs/reverse_engineering para registrar el reporte."
