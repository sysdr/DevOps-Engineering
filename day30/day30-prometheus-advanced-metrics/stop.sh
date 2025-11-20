#!/bin/bash

# Day 30: Stop Prometheus Advanced Metrics System

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=============================================="
echo "Stopping Prometheus Advanced Metrics System"
echo "=============================================="

# Stop Python app
if [ -f app.pid ]; then
    kill $(cat app.pid) 2>/dev/null || true
    rm app.pid
    echo "Stopped Python application"
fi

# Stop frontend
if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null || true
    rm frontend.pid
    echo "Stopped frontend server"
fi

# Stop Docker services
echo "Stopping Docker services..."
docker-compose down -v

echo ""
echo "System stopped successfully!"
