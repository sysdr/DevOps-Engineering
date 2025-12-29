#!/bin/bash

echo "Stopping MLOps Cost Optimizer..."

# Kill Python processes
pkill -f "python backend/main.py"
pkill -f "python3 -m http.server 3000"

# Stop and remove PostgreSQL container
docker stop mlops-postgres 2>/dev/null
docker rm mlops-postgres 2>/dev/null

echo "All services stopped"
