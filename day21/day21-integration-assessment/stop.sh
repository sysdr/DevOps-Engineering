#!/bin/bash

echo "🛑 Stopping Day 21: Phase 1 Integration & Assessment"
echo "=================================================="

# Kill backend process
if [ -f .backend_pid ]; then
    BACKEND_PID=$(cat .backend_pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🔄 Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        wait $BACKEND_PID 2>/dev/null
    fi
    rm .backend_pid
fi

# Kill frontend process
if [ -f .frontend_pid ]; then
    FRONTEND_PID=$(cat .frontend_pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🔄 Stopping frontend server (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        wait $FRONTEND_PID 2>/dev/null
    fi
    rm .frontend_pid
fi

# Kill any remaining processes on our ports
echo "🧹 Cleaning up remaining processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "📦 Deactivating virtual environment..."
    deactivate
fi

echo "✅ All services stopped successfully!"
