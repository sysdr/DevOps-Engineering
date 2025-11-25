#!/bin/bash

echo "=== Stopping EFK Stack and Services ==="

# Stop FastAPI services
if [ -f .user_service.pid ]; then
    kill $(cat .user_service.pid) 2>/dev/null
    rm .user_service.pid
fi

if [ -f .order_service.pid ]; then
    kill $(cat .order_service.pid) 2>/dev/null
    rm .order_service.pid
fi

if [ -f .payment_service.pid ]; then
    kill $(cat .payment_service.pid) 2>/dev/null
    rm .payment_service.pid
fi

# Stop Docker containers
echo "Stopping Docker containers..."
docker-compose down

echo "All services stopped."
