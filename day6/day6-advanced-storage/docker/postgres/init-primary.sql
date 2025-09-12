-- Create replication user
CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'repl_pass_123';

-- Create sample tables for testing
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(10,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    region VARCHAR(20) DEFAULT 'us-east-1'
);

CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_performance_metrics_recorded_at ON performance_metrics(recorded_at);

-- Insert sample data
INSERT INTO users (username, email) VALUES 
    ('john_doe', 'john@example.com'),
    ('jane_smith', 'jane@example.com'),
    ('bob_johnson', 'bob@example.com');

INSERT INTO transactions (user_id, amount, transaction_type) VALUES 
    (1, 100.50, 'deposit'),
    (1, -50.25, 'withdrawal'),
    (2, 200.00, 'deposit'),
    (3, -75.00, 'withdrawal');
