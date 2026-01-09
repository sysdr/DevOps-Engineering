#!/bin/bash

echo "Stopping Performance Optimization System..."

if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi

# Kill any remaining processes
pkill -f "python main.py"
pkill -f "http.server 3000"

echo "System stopped"
