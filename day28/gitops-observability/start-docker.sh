#!/bin/bash

echo "Starting with Docker Compose..."
docker-compose up --build -d

echo ""
echo "Dashboard: http://localhost:3000"
echo "API: http://localhost:8000"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop: docker-compose down"
