# Disaster Recovery (Fase 3.3)

Procedimiento para recuperar el sistema ante fallos mayores.

## Supuestos
- Se cuenta con backups recientes en `./backups`
- Acceso al servidor y a Docker

## Pasos de Recuperación (DB)
1. Detener aplicación que usa la DB
2. Restaurar con `ops/backup/restore_database.sh <backup.sql[.gz]>`
3. Verificar integridad (consultas básicas, migraciones)
4. Levantar aplicación

## Pasos de Recuperación (Redis)
1. Detener Redis
2. Restaurar con `ops/backup/restore_redis.sh <dump.rdb>`
3. Iniciar Redis
4. Validar llaves críticas (locks)

## Validación
- Healthz: `/api/v1/healthz` OK
- Métricas Prometheus sin gaps mayores a RPO
- Checks funcionales básicos (crear reserva de prueba)

## Tiempos Objetivo
- RTO: < 30 min
- RPO: < 60 min

## Checklist Post-Incidente
- Confirmar orígenes y causas
- Documentar en postmortem
- Ajustar estrategia si aplica
