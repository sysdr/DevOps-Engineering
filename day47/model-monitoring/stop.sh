#!/bin/bash

echo "Stopping Model Monitoring Platform..."

# Kill Python processes
pkill -f "python backend"
pkill -f "npm start"

# Stop Docker containers
docker stop monitoring-postgres 2>/dev/null
docker rm monitoring-postgres 2>/dev/null

echo "✅ Platform stopped"
