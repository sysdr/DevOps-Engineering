#!/bin/bash

set -e

echo "=== Starting Automation Orchestration Platform ==="

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Start backend
echo "Starting backend server..."
python backend/main.py &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 5

# Install frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install > /dev/null 2>&1
    cd ..
fi

# Start frontend
echo "Starting frontend dashboard..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=== Platform Started Successfully ==="
echo "Backend API: http://localhost:8000"
echo "Dashboard: http://localhost:3000"
echo "Metrics: http://localhost:8000/metrics"
echo ""
echo "Press Ctrl+C to stop"

# Save PIDs
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

wait
