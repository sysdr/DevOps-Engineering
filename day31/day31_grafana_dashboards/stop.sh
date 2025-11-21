#!/bin/bash

echo "Stopping all services..."

# Stop Python services
if [ -f .metrics.pid ]; then
    kill $(cat .metrics.pid) 2>/dev/null
    rm .metrics.pid
fi

if [ -f .api.pid ]; then
    kill $(cat .api.pid) 2>/dev/null
    rm .api.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi

# Stop Docker services
docker-compose down

echo "All services stopped."
