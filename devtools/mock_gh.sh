#!/usr/bin/env bash
set -euo pipefail

# Mock simple de 'gh api' para pruebas locales.
# Soporta:
#  - gh api "/repos/$OWNER/$REPO" --jq '.archived'
#  - gh api -X PATCH "/repos/$OWNER/$REPO" -f archived=true

if [ "${1:-}" != "api" ]; then
  echo "mock_gh: solo se implementa 'gh api'" >&2
  exit 2
fi
shift

METHOD="GET"
URL=""
JQ=""
ARCHIVE_FLAG="false"

while (( "$#" )); do
  case "$1" in
    -X|--method)
      METHOD="$2"; shift 2;;
    -H)
      shift 2;; # ignoramos headers
    --jq)
      JQ="$2"; shift 2;;
    -f)
      # esperamos 'archived=true'
      if [[ "$2" == "archived=true" ]]; then ARCHIVE_FLAG="true"; fi
      shift 2;;
    /*)
      URL="$1"; shift;;
    *)
      shift;;
  esac
done

# URL esperada: /repos/<owner>/<repo>
REPO_NAME="${URL##*/}"

case "$METHOD" in
  GET)
    case "$REPO_NAME" in
      SIST_CABANAS_DOCS)
        # Ya archivado
        if [[ "$JQ" == ".archived" ]]; then
          echo true
        else
          echo '{"archived":true}'
        fi
        ;;
      SIST_CABANAS)
        # No archivado
        if [[ "$JQ" == ".archived" ]]; then
          echo false
        else
          echo '{"archived":false}'
        fi
        ;;
      *)
        # Simular error (repo inexistente)
        exit 1
        ;;
    esac
    ;;
  PATCH)
    # Simular éxito al archivar si se pasó archived=true
    if [[ "$ARCHIVE_FLAG" == "true" ]]; then
      echo '{"archived":true}'
      exit 0
    else
      exit 1
    fi
    ;;
  *)
    exit 1
    ;;
esac
