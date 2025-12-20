#!/bin/bash

echo "Stopping Data Pipeline System..."

# Stop Python processes
pkill -f "airflow scheduler"
pkill -f "airflow webserver"
pkill -f "stream_processor.py"
pkill -f "uvicorn main:app"
pkill -f "react-scripts start"

# Stop Docker services
docker-compose down

echo "✓ All services stopped"
