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

# Valores por defecto; mapear desde URL si está disponible
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
run_local_redis_cli() {
  if command -v redis-cli >/dev/null 2>&1; then
    echo "[INFO] Usando redis-cli local en ${REDIS_HOST}:${REDIS_PORT}"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" BGSAVE || {
      echo "[WARN] BGSAVE falló, intentando SAVE (bloqueante)" >&2
      redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" SAVE
    }
    return 0
  fi
  return 1
}

run_docker_redis_cli() {
  local candidates=("alojamientos_redis" "redis")
  local container=""
  for c in "${candidates[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
      container="$c"; break
    fi
  done
  if [ -z "$container" ]; then
    echo "[ERROR] No se encontró un contenedor de Redis en ejecución (intentado: ${candidates[*]}). Instala redis-cli o levanta el contenedor." >&2
    return 1
  fi
  echo "[INFO] Usando docker exec en contenedor '${container}'"
  docker exec "$container" sh -lc "redis-cli --no-auth-warning ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} BGSAVE" || {
    echo "[WARN] BGSAVE falló, intentando SAVE (bloqueante)" >&2
    docker exec "$container" sh -lc "redis-cli --no-auth-warning ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} SAVE"
  }
}

if ! run_local_redis_cli; then
  run_docker_redis_cli
fi

# Ubicación del dump
get_redis_dir() {
  if command -v redis-cli >/dev/null 2>&1; then
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" CONFIG GET dir 2>/dev/null | tail -n1
    return
  fi
  local candidates=("alojamientos_redis" "redis")
  for c in "${candidates[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
      docker exec "$c" sh -lc "redis-cli --no-auth-warning ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} CONFIG GET dir" 2>/dev/null | tail -n1
      return
    fi
  done
}

REDIS_DIR=$(get_redis_dir)
DUMP_FILE="${REDIS_DIR}/dump.rdb"

# Esperar hasta 20s a que BGSAVE genere dump.rdb
WAIT_SECS=0
while [ ! -f "$DUMP_FILE" ] && [ $WAIT_SECS -lt 20 ]; do
  sleep 1
  WAIT_SECS=$((WAIT_SECS+1))
done

TARGET="${BACKUP_DIR}/redis_${DATE}.rdb"
if [ -f "$DUMP_FILE" ]; then
  cp -f "$DUMP_FILE" "$TARGET"
else
  echo "[WARN] No se encontró dump.rdb en ${REDIS_DIR} tras ${WAIT_SECS}s; intentando fallback a appendonly.aof" >&2
  if [ -f "${REDIS_DIR}/appendonly.aof" ]; then
    TARGET="${BACKUP_DIR}/redis_${DATE}.aof"
    cp -f "${REDIS_DIR}/appendonly.aof" "$TARGET"
  else
    echo "[WARN] Tampoco se encontró appendonly.aof en ${REDIS_DIR}. Intentando generar snapshot con redis-cli --rdb" >&2
    # Intentar generar RDB directamente
    gen_with_docker=0
    if command -v redis-cli >/dev/null 2>&1; then
      tmp_local="/tmp/redis_${DATE}.rdb"
      if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${AUTH_ARG[@]}" --rdb "$tmp_local"; then
        cp -f "$tmp_local" "$TARGET"
        rm -f "$tmp_local"
      else
        gen_with_docker=1
      fi
    else
      gen_with_docker=1
    fi
    if [ $gen_with_docker -eq 1 ]; then
      # Buscar contenedor de Redis
      candidates=("alojamientos_redis" "redis")
      container=""
      for c in "${candidates[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
          container="$c"; break
        fi
      done
      if [ -z "$container" ]; then
        echo "[ERROR] No se pudo generar snapshot: no hay contenedor Redis accesible" >&2
        exit 2
      fi
      tmp_in="/data/tmp-backup-${DATE}.rdb"
      if docker exec "$container" sh -lc "redis-cli --no-auth-warning ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} --rdb $tmp_in"; then
        # Copiar del contenedor al host
        docker exec "$container" sh -lc "cat $tmp_in" > "$TARGET"
        docker exec "$container" sh -lc "rm -f $tmp_in" >/dev/null 2>&1 || true
      else
        echo "[ERROR] No fue posible generar un RDB con redis-cli --rdb" >&2
        exit 2
      fi
    fi
  fi
fi

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
