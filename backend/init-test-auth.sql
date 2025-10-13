-- Script de inicialización para configurar autenticación en tests E2E
-- Este archivo se ejecuta automáticamente al iniciar el contenedor PostgreSQL

-- No es necesario modificar pg_hba.conf aquí, pero nos aseguramos de que
-- el password esté correctamente configurado
ALTER USER alojamientos_test WITH PASSWORD 'test_pass';
