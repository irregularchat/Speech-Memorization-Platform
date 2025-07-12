-- PostgreSQL initialization script for Speech Memorization Platform
-- This script sets up the database with proper extensions and configurations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database if it doesn't exist (Docker will handle this)
-- But we can set up additional configurations

-- Set timezone
SET timezone = 'UTC';

-- Create additional indexes for performance (will be applied after Django migrations)
-- These will be created by Django migrations, but we can add custom ones here if needed

-- Log the initialization
SELECT 'Speech Memorization Platform database initialized successfully' AS message;