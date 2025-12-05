#!/bin/bash

echo "Stopping all services..."

# Stop traffic generator
if [ -f traffic.pid ]; then
    kill $(cat traffic.pid) 2>/dev/null
    rm traffic.pid
fi

# Stop frontend
if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
fi

# Stop Docker services
docker compose down

echo "All services stopped."
