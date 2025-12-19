#!/bin/bash

echo "Stopping MLOps Platform..."

# Check for docker-compose (legacy) or docker compose (plugin)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "Error: Docker Compose is not installed"
    exit 1
fi

$DOCKER_COMPOSE down

echo "MLOps Platform stopped."
echo "To remove all data: $DOCKER_COMPOSE down -v"
