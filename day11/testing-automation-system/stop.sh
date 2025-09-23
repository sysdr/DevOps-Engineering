#!/bin/bash

echo "🛑 Stopping Testing Automation System..."

# Kill processes using PID files
if [ -f api.pid ]; then
    kill $(cat api.pid) 2>/dev/null
    rm api.pid
    echo "✅ Stopped API server"
fi

if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
    echo "✅ Stopped frontend server"
fi

# Kill any remaining processes
pkill -f uvicorn 2>/dev/null
pkill -f "npm start" 2>/dev/null

# Stop Docker containers
docker-compose -f docker/test-compose.yml down 2>/dev/null

echo "🎉 All services stopped!"
