#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
MOCK_GH="$HERE/mock_gh.sh"

OWNER="eevans-d"
TARGETS="${1:-SIST_CABANAS_DOCS,SIST_CABANAS}"

if [ -z "${GH_TOKEN:-}" ]; then
  echo "GH_TOKEN no configurado; abortando" >&2
  exit 1
fi

IFS=',' read -ra REPOS <<< "$TARGETS"
for R in "${REPOS[@]}"; do
  R_TRIM=$(echo "$R" | xargs)
  if [ -z "$R_TRIM" ]; then continue; fi
  CURRENT=$("$MOCK_GH" api "/repos/$OWNER/$R_TRIM" --jq '.archived' || echo "error")
  if [ "$CURRENT" = "error" ]; then
    echo "No se pudo obtener el estado de $OWNER/$R_TRIM. Se omite."
    continue
  fi
  if [ "$CURRENT" = "true" ]; then
    echo "Ya archivado: $OWNER/$R_TRIM. Se omite."
    continue
  fi
  echo "Archivando repo $OWNER/$R_TRIM ..."
  "$MOCK_GH" api -X PATCH "/repos/$OWNER/$R_TRIM" -f archived=true >/dev/null
  echo "Archivado: $OWNER/$R_TRIM"
done
echo "All requested repos archived (simulado)"
