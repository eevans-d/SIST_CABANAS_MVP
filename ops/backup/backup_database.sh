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

# Cargar .env si existe (solo POSTGRES_ y BACKUP_)
load_env_prefixes 'POSTGRES_|BACKUP_'

# Variables requeridas
: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=app}"
: "${POSTGRES_USER:=postgres}"
: "${POSTGRES_PASSWORD:=postgres}"
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

echo "[INFO] Iniciando backup ${MODE} de '${POSTGRES_DB}' desde ${POSTGRES_HOST}:${POSTGRES_PORT}"
if [[ "$MODE" == "schema-only" ]]; then
  pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -s -f "$FILEPATH"
else
  pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F p -f "$FILEPATH"
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
