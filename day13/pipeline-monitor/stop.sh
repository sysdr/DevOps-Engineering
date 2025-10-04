#!/bin/bash

echo "🛑 Stopping Pipeline Performance Monitor..."

# Kill backend
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
    echo "🐍 Backend stopped"
fi

# Kill frontend  
if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
    echo "⚛️ Frontend stopped"
fi

# Stop Redis
redis-cli shutdown 2>/dev/null || true
echo "🔴 Redis stopped"

# Kill any remaining processes
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

echo "✅ All services stopped successfully"
