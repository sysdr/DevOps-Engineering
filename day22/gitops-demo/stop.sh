#!/bin/bash

# Get absolute path of script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Stopping GitOps Demo ==="

# Kill backend process
if [ -f "$SCRIPT_DIR/.backend_pid" ]; then
    BACKEND_PID=$(cat "$SCRIPT_DIR/.backend_pid")
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm "$SCRIPT_DIR/.backend_pid"
fi

# Kill frontend process
if [ -f "$SCRIPT_DIR/.frontend_pid" ]; then
    FRONTEND_PID=$(cat "$SCRIPT_DIR/.frontend_pid")
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm "$SCRIPT_DIR/.frontend_pid"
fi

# Kill any remaining processes
echo "Cleaning up any remaining processes..."
pkill -f "python.*src.main|uvicorn.*main" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

# Kill processes on ports
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Stopping process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Stopping process on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

# Stop Docker containers
if command -v docker-compose &> /dev/null; then
    echo "Stopping Docker containers..."
    docker-compose down 2>/dev/null || true
fi

echo "✅ GitOps Demo stopped successfully!"
