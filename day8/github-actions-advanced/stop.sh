#!/bin/bash

echo "🛑 Stopping Day 8 services..."

# Stop Docker Compose services
docker-compose down

# Clean up containers and images
docker system prune -f

# Deactivate virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    deactivate
fi

echo "✅ All services stopped and cleaned up!"
