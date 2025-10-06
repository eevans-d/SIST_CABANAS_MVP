#!/usr/bin/env bash
set -euo pipefail

# restore_database.sh - Restauración de PostgreSQL desde un dump SQL o SQL.GZ
# Uso: ./restore_database.sh PATH_AL_BACKUP.sql[.gz]

if [ $# -lt 1 ]; then
  echo "Uso: $0 PATH_AL_BACKUP.sql[.gz]" >&2
  exit 1
fi

BACKUP_FILE="$1"

# Cargar .env (POSTGRES_, DB_ para compatibilidad)
if [ -f ".env" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    if printf '%s' "$line" | grep -qE '^(POSTGRES_|DB_)'; then
      key=${line%%=*}
      val=${line#*=}
      export "$key=$val"
    fi
  done < .env
fi

# Mapear variables DB_* a POSTGRES_* si no están definidas
: "${POSTGRES_DB:=${DB_NAME:-app}}"
: "${POSTGRES_USER:=${DB_USER:-postgres}}"
: "${POSTGRES_PASSWORD:=${DB_PASSWORD:-postgres}}"

: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=${DB_PORT:-5433}}"

export PGPASSWORD="$POSTGRES_PASSWORD"

echo "[INFO] Restaurando '${POSTGRES_DB}' desde ${BACKUP_FILE}"

# Detectar si usamos psql local o docker
USE_DOCKER=0
CONTAINER=""
if ! command -v psql >/dev/null 2>&1; then
  # Buscar contenedor de Postgres
  candidates=("alojamientos_postgres" "alojamientos_db" "postgres" "db")
  for c in "${candidates[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
      CONTAINER="$c"
      USE_DOCKER=1
      break
    fi
  done
  if [ $USE_DOCKER -eq 0 ]; then
    echo "[ERROR] psql no encontrado y no hay contenedor Postgres disponible" >&2
    exit 1
  fi
  echo "[INFO] Usando docker exec en contenedor '${CONTAINER}'"
fi

# Drop y recreate DB (precaución)
echo "[INFO] Terminando conexiones activas y recreando DB..."

if [ $USE_DOCKER -eq 1 ]; then
  # Ejecutar en contenedor (host y port internos al contenedor)
  docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$CONTAINER" \
    psql -h localhost -p 5432 -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${POSTGRES_DB}' AND pid <> pg_backend_pid();" || true

  docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$CONTAINER" \
    psql -h localhost -p 5432 -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\";"

  docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$CONTAINER" \
    psql -h localhost -p 5432 -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "CREATE DATABASE \"${POSTGRES_DB}\";"
else
  # Ejecutar local
  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${POSTGRES_DB}' AND pid <> pg_backend_pid();" || true

  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\";"

  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "CREATE DATABASE \"${POSTGRES_DB}\";"
fi

# Restauración
echo "[INFO] Importando datos..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
  if [ $USE_DOCKER -eq 1 ]; then
    gunzip -c "$BACKUP_FILE" | docker exec -i -e PGPASSWORD="$POSTGRES_PASSWORD" "$CONTAINER" \
      psql -h localhost -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1
  else
    gunzip -c "$BACKUP_FILE" | psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1
  fi
else
  if [ $USE_DOCKER -eq 1 ]; then
    docker exec -i -e PGPASSWORD="$POSTGRES_PASSWORD" "$CONTAINER" \
      psql -h localhost -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 < "$BACKUP_FILE"
  else
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f "$BACKUP_FILE"
  fi
fi

echo "[OK] Restauración completada"
