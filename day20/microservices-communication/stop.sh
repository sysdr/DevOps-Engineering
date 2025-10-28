#!/bin/bash

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "🛑 Stopping Microservices Communication Platform..."

# Kill Python processes
echo "🐍 Stopping Python services..."
pkill -f "python.*main.py" || true
sleep 2

# Kill React process
echo "🌐 Stopping React application..."
pkill -f "react-scripts" || true
sleep 2

# Stop Docker services
echo "🐳 Stopping Docker services..."
cd "$PROJECT_DIR/docker"
docker-compose down || true
cd "$PROJECT_DIR"

echo "✅ All services stopped successfully!"
