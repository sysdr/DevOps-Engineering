#!/bin/bash

echo "🛑 Stopping Multi-Environment Deployment Platform..."

# Kill application if PID file exists
if [ -f app.pid ]; then
    APP_PID=$(cat app.pid)
    kill $APP_PID 2>/dev/null
    rm app.pid
    echo "Application stopped"
fi

# Stop Docker services
cd infrastructure/docker
docker-compose down

echo "✅ All services stopped"
