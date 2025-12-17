#!/bin/bash

echo "Stopping Supply Chain Security System..."

if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null
    rm backend.pid
fi

if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
fi

# Kill any remaining processes
pkill -f "uvicorn app.main:app"
pkill -f "python3 -m http.server 3000"

echo "All services stopped."
