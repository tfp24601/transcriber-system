-- Database initialization script for Transcriber System
-- This runs on database container startup

-- Connect to the main_sol_db database (your existing database)
\c main_sol_db;

-- Create the transcriber schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS transcriber;

-- Set the search path to include the transcriber schema
SET search_path = transcriber, public;

-- Run the main schema
\i /docker-entrypoint-initdb.d/schema.sql

-- Run seed data (optional, for development)
-- Uncomment the next line if you want test data
-- \i /docker-entrypoint-initdb.d/seed.sql

-- Grant permissions to the ben user (your existing postgres user)
GRANT ALL PRIVILEGES ON SCHEMA transcriber TO ben;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA transcriber TO ben;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA transcriber TO ben;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA transcriber TO ben;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA transcriber GRANT ALL ON TABLES TO ben;
ALTER DEFAULT PRIVILEGES IN SCHEMA transcriber GRANT ALL ON SEQUENCES TO ben;
ALTER DEFAULT PRIVILEGES IN SCHEMA transcriber GRANT ALL ON FUNCTIONS TO ben;