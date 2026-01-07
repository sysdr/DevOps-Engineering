#!/bin/bash

echo "=== Stopping Automation Platform ==="

if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null || true
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null || true
    rm .frontend.pid
fi

# Kill any remaining processes
pkill -f "python backend/main.py" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

echo "Platform stopped"
