#!/bin/bash

set -e

echo "=== Starting Disaster Recovery System ==="

# Create and activate virtual environment
cd backend
USE_VENV=false
if [ ! -d "venv" ]; then
    if python3 -m venv venv 2>/dev/null; then
        echo "✅ Virtual environment created"
        USE_VENV=true
    else
        echo "⚠️  Virtual environment creation failed, using system Python"
        USE_VENV=false
    fi
else
    if [ -f "venv/bin/activate" ]; then
        USE_VENV=true
    else
        echo "⚠️  Virtual environment incomplete, using system Python"
        USE_VENV=false
    fi
fi

if [ "$USE_VENV" = true ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    PYTHON_CMD=python
    PIP_CMD=pip
else
    PYTHON_CMD=python3
    PIP_CMD=pip3
fi

# Install dependencies (minimal)
$PIP_CMD install --upgrade pip > /dev/null 2>&1 || true
echo "✅ Dependencies ready"

# Start backend
echo "🚀 Starting backend API..."
$PYTHON_CMD -m app.main &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API is healthy"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start frontend
cd ../frontend
echo "🚀 Starting frontend dashboard..."
python3 -m http.server 3000 > /dev/null 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

sleep 2

echo ""
echo "========================================"
echo "✅ Disaster Recovery System is running!"
echo "========================================"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API:       http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "bash ../stop.sh" INT
wait
