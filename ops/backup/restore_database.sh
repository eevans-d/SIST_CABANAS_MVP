#!/usr/bin/env bash
set -euo pipefail

# restore_database.sh - Restauración de PostgreSQL desde un dump SQL o SQL.GZ
# Uso: ./restore_database.sh PATH_AL_BACKUP.sql[.gz]

if [ $# -lt 1 ]; then
  echo "Uso: $0 PATH_AL_BACKUP.sql[.gz]" >&2
  exit 1
fi

BACKUP_FILE="$1"

# Cargar .env (solo POSTGRES_)
if [ -f ".env" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    if printf '%s' "$line" | grep -qE '^(POSTGRES_)'; then
      key=${line%%=*}
      val=${line#*=}
      export "$key=$val"
    fi
  done < .env
fi

: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=app}"
: "${POSTGRES_USER:=postgres}"
: "${POSTGRES_PASSWORD:=postgres}"

export PGPASSWORD="$POSTGRES_PASSWORD"

echo "[INFO] Restaurando '${POSTGRES_DB}' desde ${BACKUP_FILE}"

# Drop y recreate DB (precaución)
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${POSTGRES_DB}' AND pid <> pg_backend_pid();" || true
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\";"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${POSTGRES_DB}\";"

# Restauración
if [[ "$BACKUP_FILE" == *.gz ]]; then
  gunzip -c "$BACKUP_FILE" | psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1
else
  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f "$BACKUP_FILE"
fi

echo "[OK] Restauración completada"
