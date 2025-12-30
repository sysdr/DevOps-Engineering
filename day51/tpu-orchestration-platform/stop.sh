#!/bin/bash

echo "Stopping TPU Orchestration Platform..."

# Kill backend
if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null
    rm backend.pid
    echo "✓ Backend stopped"
fi

# Kill frontend
if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
    echo "✓ Frontend stopped"
fi

# Kill any remaining processes
pkill -f "python app/main.py" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null

echo "✓ All services stopped"
