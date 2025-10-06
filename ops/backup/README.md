# Backups & Disaster Recovery - Ops

## Scripts
- `backup_database.sh`: Backup PostgreSQL (full/schema-only) con `--gzip` y `--keep N` (rotación).
- `restore_database.sh`: Restaurar PostgreSQL desde `.sql` o `.sql.gz` (drop/recreate seguro).
- `backup_redis.sh`: Backup Redis (BGSAVE/SAVE) con `--keep N`.
- `restore_redis.sh`: Restaurar Redis desde `.rdb`.

Variables (en `.env`):
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- `BACKUP_DIR` (default `./backups`), `BACKUP_KEEP` (default `7`)

## Uso rápido
```bash
# Crear backups
make backup-db
make backup-redis

# Restaurar (DB y Redis)
make restore-db FILE=backups/postgres/pg_app_full_2025-10-06_10-00-00.sql.gz
make restore-redis FILE=backups/redis/redis_2025-10-06_10-00-00.rdb
```

## Cron jobs
Ver `ops/backup/cron_examples.txt` para ejemplos diarios (02:00 DB, 02:10 Redis).

## Notas
- Verificar espacio en disco suficiente en `BACKUP_DIR`.
- Probar restoraciones en un entorno aislado semanalmente.
- Considerar cifrado y almacenamiento remoto (S3) post-MVP.
