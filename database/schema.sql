-- Create database aegis;
-- \c aegis;

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sensors (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id),
    type VARCHAR(100),
    location GEOMETRY(POINT, 4326),
    last_reading JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    sensor_id INT REFERENCES sensors(id),
    event_type VARCHAR(100),
    data_hash VARCHAR(255),
    blockchain_tx VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);