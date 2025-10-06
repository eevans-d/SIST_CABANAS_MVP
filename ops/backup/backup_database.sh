#!/usr/bin/env bash
set -euo pipefail

# backup_database.sh - Backup de PostgreSQL con rotación y verificación básica
# Uso: ./backup_database.sh [--full|--schema-only] [--gzip] [--keep N]

DATE=$(date +"%Y-%m-%d_%H-%M-%S")
MODE="full"    # full | schema-only
COMPRESS=0
KEEP=7

# Función: cargar variables de .env con prefijos permitidos
load_env_prefixes() {
  # $1: regex de prefijos, ej: 'POSTGRES_|BACKUP_'
  local prefixes_regex="$1"
  if [ -f ".env" ]; then
    while IFS= read -r line; do
      # ignorar comentarios y líneas vacías
      [ -z "$line" ] && continue
      case "$line" in \#*) continue ;; esac
      # solo líneas que comienzan con los prefijos
      if printf '%s' "$line" | grep -qE "^(${prefixes_regex})"; then
        # separar clave=valor preservando '=' en el valor
        key=${line%%=*}
        val=${line#*=}
        export "$key=$val"
      fi
    done < .env
  fi
}

# Cargar .env si existe (POSTGRES_, BACKUP_ y DB_ para compatibilidad)
load_env_prefixes 'POSTGRES_|BACKUP_|DB_'

# Mapear variables DB_* a POSTGRES_* si no están definidas
: "${POSTGRES_DB:=${DB_NAME:-app}}"
: "${POSTGRES_USER:=${DB_USER:-postgres}}"
: "${POSTGRES_PASSWORD:=${DB_PASSWORD:-postgres}}"

# Variables requeridas
: "${POSTGRES_HOST:=localhost}"
# Puerto por defecto: 5433 si usamos docker-compose de raíz, 5432 en otros casos
: "${POSTGRES_PORT:=${DB_PORT:-5433}}"
: "${BACKUP_DIR:=./backups/postgres}"

mkdir -p "$BACKUP_DIR"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --full) MODE="full"; shift ;;
    --schema-only) MODE="schema-only"; shift ;;
    --gzip) COMPRESS=1; shift ;;
    --keep) KEEP="$2"; shift 2 ;;
    *) echo "Argumento no reconocido: $1"; exit 1 ;;
  esac
done

FILENAME="pg_${POSTGRES_DB}_${MODE}_${DATE}.sql"
FILEPATH="${BACKUP_DIR}/${FILENAME}"

export PGPASSWORD="$POSTGRES_PASSWORD"

echo "[INFO] Iniciando backup ${MODE} de '${POSTGRES_DB}'"

# Construir argumentos comunes de pg_dump
PG_DUMP_ARGS=("-U" "$POSTGRES_USER" "-d" "$POSTGRES_DB" "-F" "p")
if [[ "$MODE" == "schema-only" ]]; then
  PG_DUMP_ARGS=("-U" "$POSTGRES_USER" "-d" "$POSTGRES_DB" "-s")
fi

run_local_pg_dump() {
  if command -v pg_dump >/dev/null 2>&1; then
    echo "[INFO] Usando pg_dump local en ${POSTGRES_HOST}:${POSTGRES_PORT}"
    if [[ "$MODE" == "schema-only" ]]; then
      pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" "${PG_DUMP_ARGS[@]}" -f "$FILEPATH"
    else
      pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" "${PG_DUMP_ARGS[@]}" -f "$FILEPATH"
    fi
    return 0
  fi
  return 1
}

run_docker_pg_dump() {
  # Intentar con contenedores comunes
  local candidates=("alojamientos_postgres" "alojamientos_db" "postgres" "db")
  local container=""
  for c in "${candidates[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
      container="$c"; break
    fi
  done
  if [ -z "$container" ]; then
    echo "[ERROR] No se encontró un contenedor de Postgres en ejecución (intentado: ${candidates[*]}). Instala pg_dump o levanta el contenedor." >&2
    return 1
  fi
  echo "[INFO] Usando docker exec en contenedor '${container}'"
  # Redirigir salida a archivo en host
  if [[ "$MODE" == "schema-only" ]]; then
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$container" \
      sh -lc "pg_dump -h localhost -p 5432 ${PG_DUMP_ARGS[*]}" > "$FILEPATH"
  else
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$container" \
      sh -lc "pg_dump -h localhost -p 5432 ${PG_DUMP_ARGS[*]}" > "$FILEPATH"
  fi
}

if ! run_local_pg_dump; then
  run_docker_pg_dump
fi

if [[ "$COMPRESS" -eq 1 ]]; then
  gzip -9 "$FILEPATH"
  FILEPATH="${FILEPATH}.gz"
fi

echo "[INFO] Backup generado: ${FILEPATH}"

# Verificación básica: archivo no vacío
if [ ! -s "$FILEPATH" ]; then
  echo "[ERROR] El archivo de backup está vacío" >&2
  exit 2
fi

# Rotación: mantener últimos N backups (manejo seguro de nombres)
if [[ "$KEEP" =~ ^[0-9]+$ ]]; then
  echo "[INFO] Manteniendo últimos ${KEEP} backups en ${BACKUP_DIR}"
  # shellcheck disable=SC2012
  mapfile -t files < <(ls -1t "${BACKUP_DIR}"/pg_"${POSTGRES_DB}"_*.sql* 2>/dev/null || true)
  if (( ${#files[@]} > KEEP )); then
    to_delete=( "${files[@]:$KEEP}" )
    if (( ${#to_delete[@]} > 0 )); then
      printf '%s\0' "${to_delete[@]}" | xargs -0 -r rm -f
    fi
  fi
fi

echo "[OK] Backup completado exitosamente"
