#!/bin/bash

echo "Stopping FinOps Platform..."

if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm backend.pid
    echo "Backend stopped (PID: $BACKEND_PID)"
fi

if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm frontend.pid
    echo "Frontend stopped (PID: $FRONTEND_PID)"
fi

# Kill any remaining processes
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null

echo "FinOps Platform stopped successfully"
