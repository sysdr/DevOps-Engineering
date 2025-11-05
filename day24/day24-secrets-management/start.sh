#!/bin/bash

set -e

# Get the script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Starting Day 24 Application"
echo "=========================================="

# Check for duplicate services
echo "Checking for existing services..."
if pgrep -f "python.*api_server.py" > /dev/null; then
    echo "WARNING: Backend API server is already running!"
    echo "Killing existing backend processes..."
    pkill -f "python.*api_server.py" || true
    sleep 2
fi

if pgrep -f "react-scripts start" > /dev/null; then
    echo "WARNING: Frontend server is already running!"
    echo "Killing existing frontend processes..."
    pkill -f "react-scripts start" || true
    sleep 2
fi

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 not found, using python3"
    PYTHON_CMD=python3
else
    PYTHON_CMD=python3.11
fi

# Validate required files exist
if [ ! -f "$SCRIPT_DIR/backend/requirements.txt" ]; then
    echo "ERROR: backend/requirements.txt not found!"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/backend/api_server.py" ]; then
    echo "ERROR: backend/api_server.py not found!"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/frontend/package.json" ]; then
    echo "ERROR: frontend/package.json not found!"
    exit 1
fi

# Create and activate virtual environment
echo "Setting up virtual environment..."
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    $PYTHON_CMD -m venv "$SCRIPT_DIR/venv"
fi
source "$SCRIPT_DIR/venv/bin/activate"

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$SCRIPT_DIR/backend"
pip install -q -r requirements.txt
cd "$SCRIPT_DIR"

# Install Node dependencies
echo "Installing Node dependencies..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
cd "$SCRIPT_DIR"

# Start backend in background
echo "Starting backend server..."
cd "$SCRIPT_DIR/backend"
source "$SCRIPT_DIR/venv/bin/activate"
python api_server.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for backend to start
echo "Waiting for backend to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

# Start frontend in background
echo "Starting frontend server..."
cd "$SCRIPT_DIR/frontend"
BROWSER=none npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "=========================================="
echo "Application started successfully!"
echo "=========================================="
echo "Backend API: http://localhost:8000"
echo "Frontend Dashboard: http://localhost:3000"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  Backend: /tmp/backend.log"
echo "  Frontend: /tmp/frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; pkill -f 'react-scripts start' 2>/dev/null || true; exit" INT TERM
wait
