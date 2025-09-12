#!/bin/bash
# Stop WASM Edge Computing Platform

echo "🛑 Stopping WASM Edge Computing Platform..."

# Kill any running uvicorn processes
pkill -f "uvicorn src.main:app" || true

# Kill any running Node.js processes (for dev server)
pkill -f "react-scripts start" || true

# Stop Docker containers if running
docker-compose down || true

echo "✅ Platform stopped"
