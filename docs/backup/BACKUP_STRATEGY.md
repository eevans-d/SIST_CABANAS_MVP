# Estrategia de Backups (Fase 3.3)

Objetivo: asegurar RPO < 1h y RTO < 30 min para base de datos y Redis.

## Alcance
- PostgreSQL (base de datos principal)
- Redis (locks y llaves efímeras)

## Frecuencia y Retención
- Diario a las 02:00: backup full de PostgreSQL + snapshot Redis
- Retención: 7 días recientes, 4 semanas, 12 meses (granularidad mensual)

## Ubicación
- Local: `./backups/`
- Remoto (opcional): bucket S3/compatible (no incluido en MVP)

## Verificación
- Verificación básica: archivo no vacío, `pg_restore --list`/`psql` dry-run
- Restore de prueba semanal en entorno de staging

## Automatización
- Cron jobs o systemd timers (ver `ops/backup/cron_examples.txt`)

## Seguridad
- Variables en `.env` (no commitear credenciales)
- Permisos estrictos en directorios de backup
