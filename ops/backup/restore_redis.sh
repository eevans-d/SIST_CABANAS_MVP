#!/usr/bin/env bash
set -euo pipefail

# restore_redis.sh - Restauración de Redis desde un archivo RDB
# Uso: ./restore_redis.sh PATH_AL_RDB

if [ $# -lt 1 ]; then
  echo "Uso: $0 PATH_AL_RDB" >&2
  exit 1
fi

RDB_FILE="$1"

# Cargar .env (solo REDIS_)
if [ -f ".env" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    if printf '%s' "$line" | grep -qE '^(REDIS_)'; then
      key=${line%%=*}
      val=${line#*=}
      export "$key=$val"
    fi
  done < .env
fi

: "${REDIS_HOST:=localhost}"
: "${REDIS_PORT:=6379}"
: "${REDIS_PASSWORD:=}"

AUTH_ARG=()
if [ -n "$REDIS_PASSWORD" ]; then
  AUTH_ARG+=("-a" "$REDIS_PASSWORD")
fi

# Apagar Redis con persistencia segura
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" SHUTDOWN SAVE || true

# Determinar directorio de datos
INFO=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" CONFIG GET dir 2>/dev/null || echo -n)
REDIS_DIR=$(echo "$INFO" | tail -n1)
if [ -z "$REDIS_DIR" ]; then
  REDIS_DIR="/var/lib/redis"
fi

# Restaurar RDB
cp -f "$RDB_FILE" "${REDIS_DIR}/dump.rdb"

echo "[INFO] RDB restaurado en ${REDIS_DIR}/dump.rdb"

echo "[ACTION] Inicie nuevamente el servicio de Redis manualmente según su entorno (docker-compose, systemd, etc.)"
