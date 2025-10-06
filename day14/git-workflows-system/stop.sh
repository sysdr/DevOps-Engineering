#!/bin/bash

echo "🛑 Stopping Git Workflows Manager"

# Kill processes by PID
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm backend.pid
    echo "✅ Backend stopped"
fi

if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm frontend.pid
    echo "✅ Frontend stopped"
fi

# Kill any remaining processes
pkill -f "uvicorn.*main:app" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null

echo "🏁 All services stopped"
