#!/bin/bash

echo "🛑 Stopping Advanced GitOps Implementation..."

# Stop Docker services
docker-compose down

# Kill Flask processes
pkill -f "python web-dashboard/app.py"
pkill -f "gunicorn"

# Deactivate virtual environment
deactivate

echo "✅ All services stopped"
