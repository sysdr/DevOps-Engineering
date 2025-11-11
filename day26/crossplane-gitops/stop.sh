#!/bin/bash

echo "Stopping Crossplane Infrastructure Platform..."

# Stop API server
if [ -f .api.pid ]; then
    PID=$(cat .api.pid)
    kill $PID 2>/dev/null
    rm .api.pid
    echo "API server stopped"
else
    echo "No running API server found"
    pkill -f "python backend/crossplane_api.py"
fi

# Stop frontend server
if [ -f .frontend.pid ]; then
    PID=$(cat .frontend.pid)
    kill $PID 2>/dev/null
    rm .frontend.pid
    echo "Frontend server stopped"
else
    echo "No running frontend server found"
    pkill -f "python3 -m http.server 8080"
fi

echo "Stopped"
