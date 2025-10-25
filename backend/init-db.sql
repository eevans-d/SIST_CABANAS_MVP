-- Extensiones PostgreSQL necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Usuario de aplicación (ya creado por POSTGRES_USER)
-- El usuario 'alojamientos' ya existe y tiene permisos sobre la DB

-- Configuración adicional para mejor rendimiento
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Configuración de logs para auditoría
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s

-- Configuración de autenticación segura
ALTER SYSTEM SET password_encryption = 'scram-sha-256';

-- Timezone para Argentina
ALTER SYSTEM SET timezone = 'America/Argentina/Buenos_Aires';

-- Reload configuración
SELECT pg_reload_conf();
