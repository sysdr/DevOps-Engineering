#!/bin/bash

# Day 30: Start Prometheus Advanced Metrics System

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=============================================="
echo "Starting Prometheus Advanced Metrics System"
echo "=============================================="

# Activate virtual environment
source venv/bin/activate

# Start Docker services
echo ""
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to initialize..."
sleep 15

# Start Python application
echo ""
echo "Starting Python metrics application..."
cd app
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../app.log 2>&1 &
echo $! > ../app.pid
cd ..

# Wait for app to start
sleep 5

# Start frontend server
echo ""
echo "Starting frontend dashboard..."
cd frontend
nohup python -m http.server 3000 > ../frontend.log 2>&1 &
echo $! > ../frontend.pid
cd ..

echo ""
echo "=============================================="
echo "System Started Successfully!"
echo "=============================================="
echo ""
echo "Access Points:"
echo "  Dashboard:        http://localhost:3000"
echo "  App Metrics:      http://localhost:8000/metrics"
echo "  App API:          http://localhost:8000"
echo "  Prometheus 0:     http://localhost:9090"
echo "  Prometheus 1:     http://localhost:9091"
echo "  Thanos Query:     http://localhost:10904"
echo "  Alertmanager:     http://localhost:9093"
echo "  MinIO Console:    http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "Useful Commands:"
echo "  Generate traffic:  curl http://localhost:8000/orders/simulate?count=50"
echo "  Trigger errors:    curl http://localhost:8000/error"
echo "  View alerts:       curl http://localhost:8000/alerts"
echo ""
