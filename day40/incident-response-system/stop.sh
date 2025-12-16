#!/bin/bash

echo "Stopping Security Operations Center..."

# Kill backend
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
fi

# Kill frontend
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
fi

# Kill any remaining processes
pkill -f "python main.py"
pkill -f "react-scripts start"

echo "All services stopped"
