-- Inicialización de base de datos PostgreSQL para Sistema de Reservas
-- Este script se ejecuta automáticamente en el primer arranque del contenedor

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Configurar timezone por defecto
SET timezone = 'America/Argentina/Buenos_Aires';

-- Configurar locale para fechas en español
-- Nota: El locale se configura a nivel de initdb en docker-compose

-- Crear usuario de aplicación (opcional, para mejor seguridad)
-- DO $$
-- BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
--         CREATE ROLE app_user WITH LOGIN PASSWORD 'change_me_in_production';
--         GRANT CONNECT ON DATABASE reservas TO app_user;
--         GRANT USAGE ON SCHEMA public TO app_user;
--         GRANT CREATE ON SCHEMA public TO app_user;
--     END IF;
-- END
-- $$;

-- Optimización de configuración para aplicación de reservas
-- Estas configuraciones se pueden ajustar según el hardware disponible

-- Para mejor performance en consultas de fechas
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_cache_size = '512MB';
ALTER SYSTEM SET shared_buffers = '128MB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Para mejor concurrencia en reservas
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- Logging optimizado para producción
ALTER SYSTEM SET log_destination = 'stderr';
ALTER SYSTEM SET log_statement = 'ddl';
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s

-- Reload configuration
SELECT pg_reload_conf();

-- Crear índices útiles para el esquema de la aplicación
-- Nota: Los índices principales se crean automáticamente con las migraciones Alembic
-- Estos son índices adicionales para optimización

-- Función para crear índices de forma segura
CREATE OR REPLACE FUNCTION create_index_if_not_exists(index_name text, table_name text, index_definition text)
RETURNS void AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = index_name) THEN
        EXECUTE format('CREATE INDEX %I ON %I %s', index_name, table_name, index_definition);
        RAISE NOTICE 'Index % created', index_name;
    ELSE
        RAISE NOTICE 'Index % already exists', index_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Script de mantenimiento para ejecutar periódicamente
-- Crear función para limpiar reservas expiradas automáticamente
CREATE OR REPLACE FUNCTION cleanup_expired_reservations()
RETURNS integer AS $$
DECLARE
    affected_rows integer;
BEGIN
    UPDATE reservations
    SET reservation_status = 'expired',
        updated_at = NOW()
    WHERE reservation_status = 'pre_reserved'
      AND expires_at < NOW()
      AND reservation_status != 'expired';

    GET DIAGNOSTICS affected_rows = ROW_COUNT;

    IF affected_rows > 0 THEN
        INSERT INTO system_logs (level, message, metadata, created_at)
        VALUES ('INFO', 'Expired reservations cleaned up',
                json_build_object('affected_rows', affected_rows), NOW());
    END IF;

    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql;

-- Crear tabla de logs del sistema si no existe
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para logs del sistema
SELECT create_index_if_not_exists(
    'idx_system_logs_created_at',
    'system_logs',
    '(created_at DESC)'
);

SELECT create_index_if_not_exists(
    'idx_system_logs_level',
    'system_logs',
    '(level)'
);

-- Función para limpiar logs antiguos (retener últimos 30 días)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS integer AS $$
DECLARE
    affected_rows integer;
BEGIN
    DELETE FROM system_logs
    WHERE created_at < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS affected_rows = ROW_COUNT;

    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql;

-- Vistas útiles para monitoring y reportes
CREATE OR REPLACE VIEW reservation_summary AS
SELECT
    COUNT(*) as total_reservations,
    COUNT(*) FILTER (WHERE reservation_status = 'confirmed') as confirmed_reservations,
    COUNT(*) FILTER (WHERE reservation_status = 'pre_reserved') as pending_reservations,
    COUNT(*) FILTER (WHERE reservation_status = 'expired') as expired_reservations,
    COUNT(*) FILTER (WHERE reservation_status = 'cancelled') as cancelled_reservations,
    SUM(total_price) FILTER (WHERE reservation_status = 'confirmed') as confirmed_revenue,
    AVG(total_price) FILTER (WHERE reservation_status = 'confirmed') as avg_reservation_value,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as reservations_today,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as reservations_week,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as reservations_month
FROM reservations;

CREATE OR REPLACE VIEW accommodation_utilization AS
SELECT
    a.id,
    a.name,
    a.type,
    COUNT(r.id) as total_reservations,
    COUNT(r.id) FILTER (WHERE r.reservation_status = 'confirmed') as confirmed_bookings,
    SUM(r.total_price) FILTER (WHERE r.reservation_status = 'confirmed') as total_revenue,
    AVG(r.total_price) FILTER (WHERE r.reservation_status = 'confirmed') as avg_booking_value,
    MAX(r.created_at) as last_booking_date
FROM accommodations a
LEFT JOIN reservations r ON a.id = r.accommodation_id
GROUP BY a.id, a.name, a.type
ORDER BY total_revenue DESC NULLS LAST;

-- Grant permissions en las vistas
GRANT SELECT ON reservation_summary TO PUBLIC;
GRANT SELECT ON accommodation_utilization TO PUBLIC;

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully';
    RAISE NOTICE 'Extensions created: uuid-ossp, btree_gist';
    RAISE NOTICE 'Utility functions created: cleanup_expired_reservations, cleanup_old_logs';
    RAISE NOTICE 'Views created: reservation_summary, accommodation_utilization';
    RAISE NOTICE 'System ready for application startup';
END;
$$;
