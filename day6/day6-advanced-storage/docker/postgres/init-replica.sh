#!/bin/bash
set -e

# Wait for primary to be ready
until pg_isready -h postgres-primary -p 5432 -U admin; do
  echo "Waiting for primary database..."
  sleep 2
done

# Stop PostgreSQL service
pg_ctl stop -D /var/lib/postgresql/data -m fast || true

# Remove existing data
rm -rf /var/lib/postgresql/data/*

# Create base backup from primary
export PGPASSWORD=repl_pass_123
pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U replicator -v -P

# Create standby.signal
touch /var/lib/postgresql/data/standby.signal

# Configure replica
cat >> /var/lib/postgresql/data/postgresql.conf << 'CONF'
primary_conninfo = 'host=postgres-primary port=5432 user=replicator password=repl_pass_123'
max_connections = 200
CONF

# Start PostgreSQL
pg_ctl start -D /var/lib/postgresql/data
