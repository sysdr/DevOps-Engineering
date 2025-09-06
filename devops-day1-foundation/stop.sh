#!/bin/bash

# DevOps Foundation Day 1 - Stop Script
echo "🛑 Stopping DevOps Foundation Day 1 services..."

# Stop backend
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "🖥️ Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm .backend.pid
    else
        echo "Backend process not running"
        rm -f .backend.pid
    fi
fi

# Stop frontend
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🌐 Stopping frontend server (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm .frontend.pid
    else
        echo "Frontend process not running"
        rm -f .frontend.pid
    fi
fi

# Clean up any remaining processes
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

# Deactivate virtual environment if active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    deactivate
fi

echo "✅ All services stopped"
