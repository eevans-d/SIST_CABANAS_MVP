#!/bin/bash
# Script para crear índices de performance manualmente
# Si Alembic tiene problemas de autenticación, usar este script

set -e

echo "🔧 Creando índices de performance en PostgreSQL..."

# Conectar a la base de datos y crear índices
docker-compose -f docker-compose.staging.yml exec -T db psql -U alojamientos -d alojamientos << 'EOF'

-- O6: Partial index para expired pre-reservations cleanup
-- Background job solo busca pre_reserved
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservation_expires_prereserved
ON reservations (expires_at)
WHERE reservation_status = 'pre_reserved';

-- O7: Composite index para admin queries con status+dates
-- Admin dashboard filtra por status + date range frecuentemente
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservation_status_dates
ON reservations (reservation_status, check_in, check_out);

-- Verificar que índices fueron creados
\di idx_reservation_expires_prereserved
\di idx_reservation_status_dates

-- Mostrar tamaños de índices
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('idx_reservation_expires_prereserved', 'idx_reservation_status_dates');

EOF

echo "✅ Índices de performance creados exitosamente"
