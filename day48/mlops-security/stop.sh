#!/bin/bash

echo "Stopping MLOps Security & Governance Platform..."

# Kill backend
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null || true
    rm .backend.pid
fi

# Kill frontend
if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null || true
    rm .frontend.pid
fi

# Kill any remaining processes
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true

echo "✅ All services stopped"
