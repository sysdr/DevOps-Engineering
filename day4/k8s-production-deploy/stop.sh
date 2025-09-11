#!/bin/bash

echo "🛑 Stopping Kubernetes Production Dashboard"
echo "========================================="

# Stop backend
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "🔧 Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm backend.pid
    else
        echo "⚠️ Backend process not found"
        rm -f backend.pid
    fi
else
    echo "⚠️ Backend PID file not found"
fi

# Stop frontend
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "🌐 Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm frontend.pid
    else
        echo "⚠️ Frontend process not found"
        rm -f frontend.pid
    fi
else
    echo "⚠️ Frontend PID file not found"
fi

# Kill any remaining node processes
pkill -f "react-scripts start" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

echo "✅ All services stopped"
