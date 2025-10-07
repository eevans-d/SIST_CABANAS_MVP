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

echo "[INFO] Restaurando Redis desde ${RDB_FILE}"

# Función para ejecutar redis-cli
run_redis_cli() {
  local cmd="$*"
  if command -v redis-cli >/dev/null 2>&1; then
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" "$cmd"
  else
    candidates=("alojamientos_redis" "redis")
    container=""
    for c in "${candidates[@]}"; do
      if docker ps --format '{{.Names}' | grep -q "^${c}$"; then
        container="$c"; break
      fi
    done
    if [ -z "$container" ]; then
      echo "[ERROR] redis-cli no encontrado y no hay contenedor Redis disponible" >&2
      return 1
    fi
    docker exec "$container" sh -lc "redis-cli --no-auth-warning ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} $cmd"
  fi
}

# Apagar Redis con persistencia segura
echo "[INFO] Deteniendo Redis para copiar RDB..."
run_redis_cli SHUTDOWN SAVE || true

sleep 2

# Determinar directorio de datos y copiar RDB
if command -v redis-cli >/dev/null 2>&1; then
  INFO=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" CONFIG GET dir 2>/dev/null || echo -n)
  REDIS_DIR=$(echo "$INFO" | tail -n1)
  if [ -z "$REDIS_DIR" ]; then
    REDIS_DIR="/var/lib/redis"
  fi
  cp -f "$RDB_FILE" "${REDIS_DIR}/dump.rdb"
  echo "[INFO] RDB restaurado en ${REDIS_DIR}/dump.rdb"
else
  # Docker: copiar al contenedor
  candidates=("alojamientos_redis" "redis")
  container=""
  for c in "${candidates[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${c}$"; then
      container="$c"; break
    fi
  done
  if [ -z "$container" ]; then
    echo "[ERROR] No se encontró contenedor Redis para copiar RDB" >&2
    exit 1
  fi
  docker cp "$RDB_FILE" "${container}:/data/dump.rdb"
  echo "[INFO] RDB copiado al contenedor ${container}:/data/dump.rdb"
fi

echo "[ACTION] Inicie nuevamente el servicio de Redis manualmente según su entorno (docker-compose, systemd, etc.)"
