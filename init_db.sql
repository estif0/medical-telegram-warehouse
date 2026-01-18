-- Initialize database schemas for Medical Telegram Warehouse

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA raw TO warehouse_user;
GRANT ALL PRIVILEGES ON SCHEMA staging TO warehouse_user;
GRANT ALL PRIVILEGES ON SCHEMA marts TO warehouse_user;

-- Set search path
ALTER DATABASE medical_warehouse SET search_path TO marts, staging, raw, public;
