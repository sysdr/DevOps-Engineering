#!/bin/bash

echo "Stopping services..."

if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi

# Kill any remaining processes
pkill -f "python backend/main.py"
pkill -f "react-scripts start"

echo "All services stopped."
