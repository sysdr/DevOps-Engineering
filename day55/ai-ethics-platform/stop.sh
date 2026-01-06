#!/bin/bash

echo "Stopping AI Ethics & Governance Platform..."

# Stop all Python processes
pkill -f "python src/main.py"

# Stop Node.js
pkill -f "react-scripts"

# Stop Docker services
docker-compose down

# Deactivate virtual environment
deactivate 2>/dev/null || true

echo "All services stopped!"
