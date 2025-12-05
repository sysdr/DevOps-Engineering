#!/bin/bash

echo "========================================"
echo "Starting SLO & Error Budget System"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if command -v lsof > /dev/null 2>&1; then
        lsof -i :$port > /dev/null 2>&1
    elif command -v netstat > /dev/null 2>&1; then
        netstat -tuln | grep -q ":$port "
    elif command -v ss > /dev/null 2>&1; then
        ss -tuln | grep -q ":$port "
    else
        return 1
    fi
}

# Check for port conflicts
echo "Checking for port conflicts..."
CONFLICTS=0
for port in 8001 8002 8003 8004 8005 8006 6380 9090 3000; do
    if check_port $port; then
        echo "Warning: Port $port is already in use"
        CONFLICTS=1
    fi
done

if [ $CONFLICTS -eq 1 ]; then
    echo "Some ports are in use. Attempting to stop existing services..."
    if [ -f stop.sh ]; then
        ./stop.sh
        sleep 5
    fi
fi

# Check if frontend is already running
if check_port 3000; then
    echo "Frontend is already running on port 3000. Skipping frontend start."
    SKIP_FRONTEND=1
else
    SKIP_FRONTEND=0
fi

# Build and start services
echo "Building and starting services with Docker Compose..."
DOCKER_BUILDKIT=0 docker compose up -d --build

# Wait for services to be ready with retries
echo "Waiting for services to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    READY_COUNT=0
    for port in 8001 8002 8003 8004 8005 8006; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            READY_COUNT=$((READY_COUNT + 1))
        fi
    done
    
    if [ $READY_COUNT -eq 6 ]; then
        echo "All services are ready!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        sleep 2
        echo "Waiting for services... ($RETRY_COUNT/$MAX_RETRIES)"
    fi
done

# Check service health
echo ""
echo "Checking service health..."
for port in 8001 8002 8003 8004 8005 8006; do
    echo -n "Checking port $port... "
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✓ Ready"
    else
        echo "✗ Not ready"
    fi
done

# Start frontend if not already running
if [ $SKIP_FRONTEND -eq 0 ]; then
    echo ""
    echo "Starting React frontend..."
    cd frontend
    if [ ! -d node_modules ]; then
        npm install --silent
    fi
    npm start > /dev/null 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    echo "Frontend started with PID $FRONTEND_PID"
    cd ..
else
    echo ""
    echo "Frontend is already running, skipping..."
fi

echo ""
echo "========================================"
echo "All services started successfully!"
echo "========================================"
echo ""
echo "Services:"
echo "  - Order Service: http://localhost:8001"
echo "  - Payment Service: http://localhost:8002"
echo "  - Inventory Service: http://localhost:8003"
echo "  - Notification Service: http://localhost:8004"
echo "  - SLO Calculator: http://localhost:8005"
echo "  - Policy Engine: http://localhost:8006"
echo "  - Prometheus: http://localhost:9090"
echo "  - Dashboard: http://localhost:3000"
echo ""
echo "Starting traffic generator..."
python3 scripts/traffic_generator.py &
TRAFFIC_PID=$!
echo $TRAFFIC_PID > traffic.pid

echo ""
echo "To stop all services, run: ./stop.sh"
echo "========================================"
