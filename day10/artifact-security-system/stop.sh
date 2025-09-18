#!/bin/bash
echo "🛑 Stopping Artifact Security System..."

# Kill backend and frontend
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null  
    rm .frontend.pid
fi

# Stop Harbor registry
docker-compose -f docker/docker-compose.yml down

echo "✅ System stopped successfully!"
