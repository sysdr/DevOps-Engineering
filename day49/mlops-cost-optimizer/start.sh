#!/bin/bash

echo "Starting MLOps Cost Optimizer..."

# Check and start PostgreSQL with Docker
if docker ps -a --format '{{.Names}}' | grep -q "^mlops-postgres$"; then
    if docker ps --format '{{.Names}}' | grep -q "^mlops-postgres$"; then
        echo "PostgreSQL container is already running"
    else
        echo "Starting existing PostgreSQL container..."
        docker start mlops-postgres
    fi
else
    echo "Creating and starting PostgreSQL container..."
    docker run -d --name mlops-postgres \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=mlops_costs \
        -p 5433:5432 \
        timescale/timescaledb:latest-pg14
fi

echo "Waiting for PostgreSQL to start..."
sleep 5

# Activate virtual environment
source venv/bin/activate

# Check and start backend
if lsof -i :8000 >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ':8000' || ss -tuln 2>/dev/null | grep -q ':8000'; then
    echo "Backend server is already running on port 8000"
    BACKEND_PID=""
else
    echo "Starting backend server..."
    python backend/main.py &
    BACKEND_PID=$!
fi

# Wait for backend to start
sleep 5

# Check and start frontend
if lsof -i :3000 >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ':3000' || ss -tuln 2>/dev/null | grep -q ':3000'; then
    echo "Frontend server is already running on port 3000"
    FRONTEND_PID=""
else
    echo "Starting frontend dashboard..."
    cd frontend
    python3 -m http.server 3000 --directory public &
    FRONTEND_PID=$!
    cd ..
fi

echo ""
echo "=========================================="
echo "MLOps Cost Optimizer is running!"
echo "=========================================="
echo "Backend API: http://localhost:8000"
echo "Frontend Dashboard: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
cleanup() {
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    docker stop mlops-postgres 2>/dev/null
    docker rm mlops-postgres 2>/dev/null
    exit
}
trap cleanup INT
wait
