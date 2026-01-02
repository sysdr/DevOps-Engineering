CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS metrics (
    time TIMESTAMPTZ NOT NULL,
    node_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    labels JSONB
);

SELECT create_hypertable('metrics', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_metrics_node_time ON metrics (node_name, time DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON metrics (metric_name, time DESC);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    deployment TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    predicted_value DOUBLE PRECISION NOT NULL,
    confidence_lower DOUBLE PRECISION NOT NULL,
    confidence_upper DOUBLE PRECISION NOT NULL,
    horizon_minutes INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMPTZ NOT NULL,
    metric_name TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    expected_value DOUBLE PRECISION NOT NULL,
    severity TEXT NOT NULL,
    detector_votes JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    title TEXT NOT NULL,
    symptoms JSONB NOT NULL,
    root_cause TEXT,
    remediation_actions JSONB,
    status TEXT NOT NULL,
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS scaling_decisions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    deployment TEXT NOT NULL,
    current_replicas INTEGER NOT NULL,
    target_replicas INTEGER NOT NULL,
    reason TEXT NOT NULL,
    predicted_load DOUBLE PRECISION NOT NULL,
    executed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    model_name TEXT NOT NULL,
    mae DOUBLE PRECISION NOT NULL,
    rmse DOUBLE PRECISION NOT NULL,
    accuracy DOUBLE PRECISION NOT NULL
);
