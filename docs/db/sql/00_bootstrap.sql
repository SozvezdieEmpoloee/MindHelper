-- Run this file as PostgreSQL superuser (for example: postgres)
-- It creates application role + database (idempotent).

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mindhelper_app') THEN
        CREATE ROLE mindhelper_app LOGIN PASSWORD 'MindHelper_2026!';
    END IF;
END
$$;

SELECT 'CREATE DATABASE mindhelper_db OWNER mindhelper_app ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'mindhelper_db')
\gexec

GRANT ALL PRIVILEGES ON DATABASE mindhelper_db TO mindhelper_app;
mindhelper_app
StrPass999!