#!/bin/bash

echo "🛑 Stopping Day 18 services..."

# Kill backend process
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null || true
    rm .backend.pid
    echo "✅ Backend monitoring service stopped"
fi

# Kill frontend process
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null || true
    rm .frontend.pid
    echo "✅ Frontend dashboard stopped"
fi

# Kill any remaining Node.js processes
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "node.*start" 2>/dev/null || true

echo "🏁 All services stopped"
