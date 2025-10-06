#!/usr/bin/env bash
set -euo pipefail

# backup_redis.sh - Backup de Redis usando SAVE o BGSAVE según configuración
# Uso: ./backup_redis.sh [--dir DIR] [--keep N]

DATE=$(date +"%Y-%m-%d_%H-%M-%S")
KEEP=7

# Función: cargar variables de .env con prefijos permitidos
load_env_prefixes() {
  local prefixes_regex="$1"
  if [ -f ".env" ]; then
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      case "$line" in \#*) continue ;; esac
      if printf '%s' "$line" | grep -qE "^(${prefixes_regex})"; then
        key=${line%%=*}
        val=${line#*=}
        export "$key=$val"
      fi
    done < .env
  fi
}

# Cargar .env si existe (REDIS_ y BACKUP_)
load_env_prefixes 'REDIS_|BACKUP_'

: "${REDIS_HOST:=localhost}"
: "${REDIS_PORT:=6379}"
: "${REDIS_PASSWORD:=}"
: "${BACKUP_DIR:=./backups/redis}"

mkdir -p "$BACKUP_DIR"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) BACKUP_DIR="$2"; shift 2 ;;
    --keep) KEEP="$2"; shift 2 ;;
    *) echo "Argumento no reconocido: $1"; exit 1 ;;
  esac
done

AUTH_ARG=()
if [ -n "$REDIS_PASSWORD" ]; then
  AUTH_ARG+=("-a" "$REDIS_PASSWORD")
fi

# Forzar snapshot
echo "[INFO] Solicitando BGSAVE a Redis ${REDIS_HOST}:${REDIS_PORT}"
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" BGSAVE || {
  echo "[WARN] BGSAVE falló, intentando SAVE (bloqueante)" >&2
  redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" SAVE
}

# Ubicación del dump
INFO=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" CONFIG GET dir 2>/dev/null)
REDIS_DIR=$(echo "$INFO" | tail -n1)
DUMP_FILE="${REDIS_DIR}/dump.rdb"

if [ ! -f "$DUMP_FILE" ]; then
  echo "[ERROR] No se encontró dump.rdb en ${REDIS_DIR}" >&2
  exit 2
fi

TARGET="${BACKUP_DIR}/redis_${DATE}.rdb"
cp -f "$DUMP_FILE" "$TARGET"

echo "[INFO] Backup generado: ${TARGET}"

# Rotación segura
if [[ "$KEEP" =~ ^[0-9]+$ ]]; then
  echo "[INFO] Manteniendo últimos ${KEEP} backups en ${BACKUP_DIR}"
  # shellcheck disable=SC2012
  mapfile -t files < <(ls -1t "${BACKUP_DIR}"/redis_*.rdb 2>/dev/null || true)
  if (( ${#files[@]} > KEEP )); then
    to_delete=( "${files[@]:$KEEP}" )
    if (( ${#to_delete[@]} > 0 )); then
      printf '%s\0' "${to_delete[@]}" | xargs -0 -r rm -f
    fi
  fi
fi

echo "[OK] Backup de Redis completado"
