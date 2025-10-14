-- ============================================================================
-- PostgreSQL Extensions Required for Sistema MVP
-- ============================================================================
--
-- Este script se ejecuta automáticamente al inicializar la DB en producción
-- Las extensiones son OBLIGATORIAS para el funcionamiento correcto del sistema
--

-- btree_gist: Requerido para constraint anti doble-booking
-- Permite EXCLUDE constraints con operadores &&, =, etc.
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- uuid-ossp: Generación de UUIDs (usado en códigos de reserva)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pg_trgm: Búsquedas fuzzy para nombres de huéspedes (opcional)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- unaccent: Normalización de texto para búsquedas (opcional)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- ============================================================================
-- Verificación de Extensiones
-- ============================================================================

-- Verificar que btree_gist esté disponible (CRÍTICO)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'btree_gist') THEN
        RAISE EXCEPTION 'Extension btree_gist is required but not installed';
    END IF;
    
    RAISE NOTICE 'Extension btree_gist is installed - anti double-booking ready';
END $$;

-- ============================================================================
-- Configuración de Performance (Opcional)
-- ============================================================================

-- Configuraciones optimizadas para workload de reservas
-- (Solo si no están configuradas en postgresql.conf)

-- Aumentar shared_buffers para mejor cache
-- ALTER SYSTEM SET shared_buffers = '256MB';

-- Configurar checkpoint para mejor write performance
-- ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- Configurar work_mem para ordenamientos
-- ALTER SYSTEM SET work_mem = '16MB';

-- Log de queries lentas para debugging
-- ALTER SYSTEM SET log_min_duration_statement = '1000';  -- 1 segundo

-- Reload configuration
-- SELECT pg_reload_conf();