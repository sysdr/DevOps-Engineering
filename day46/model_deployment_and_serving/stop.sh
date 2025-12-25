#!/bin/bash

echo "Stopping Model Serving Platform..."

# Stop frontend
pkill -f "vite"

# Stop backend
pkill -f "uvicorn"

# Stop Redis
redis-cli shutdown 2>/dev/null || true

echo "Services stopped."
