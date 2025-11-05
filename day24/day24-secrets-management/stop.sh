#!/bin/bash

echo "Stopping all services..."

# Kill backend
pkill -f "python api_server.py" || true

# Kill frontend
pkill -f "react-scripts start" || true

# Kill node processes
pkill -f "node" || true

echo "All services stopped"
