#!/bin/bash

echo "🛑 Stopping Docker services"
docker-compose down

echo "🧹 Cleaning up Docker resources"
docker-compose down --volumes --remove-orphans

echo "✅ Docker services stopped and cleaned up"
