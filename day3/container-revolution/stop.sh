#!/bin/bash

echo "🛑 Stopping Container Revolution Platform"

# Stop backend server
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    kill $BACKEND_PID 2>/dev/null || true
    rm logs/backend.pid
    echo "✅ Backend server stopped"
fi

# Stop frontend server
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    kill $FRONTEND_PID 2>/dev/null || true
    rm logs/frontend.pid
    echo "✅ Frontend server stopped"
fi

# Clean up containers
echo "🧹 Cleaning up containers"
podman rm -f $(podman ps -aq) 2>/dev/null || true

echo "🎯 All services stopped"
