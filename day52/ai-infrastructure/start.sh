#!/bin/bash

echo "Starting AI Infrastructure Management Platform..."

# Activate virtual environment
source venv/bin/activate

# Start TimescaleDB
echo "Starting TimescaleDB..."
docker stop timescaledb-ai 2>/dev/null || true
docker rm timescaledb-ai 2>/dev/null || true
docker run -d --name timescaledb-ai \
  -p 5433:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postgres \
  timescale/timescaledb:latest-pg15

# Wait for database
echo "Waiting for database..."
for i in {1..30}; do
    if docker exec timescaledb-ai pg_isready -U postgres > /dev/null 2>&1; then
        echo "Database is ready!"
        break
    fi
    echo "Waiting for database... ($i/30)"
    sleep 1
done

# Initialize schema
echo "Initializing database schema..."
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d postgres -f backend/schema.sql || echo "Schema may already exist"

# Start metrics collector
echo "Starting metrics collector..."
python backend/collectors/metrics_collector.py &
COLLECTOR_PID=$!

# Start API server
echo "Starting API server..."
PYTHONPATH=$(pwd)/backend:$PYTHONPATH uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start frontend
echo "Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "✅ AI Infrastructure Management Platform Started"
echo "============================================"
echo "API Server: http://localhost:8000"
echo "Dashboard: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Save PIDs
echo $COLLECTOR_PID > .pids
echo $API_PID >> .pids
echo $FRONTEND_PID >> .pids

# Wait
wait
