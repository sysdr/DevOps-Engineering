#!/bin/bash

echo "=== Starting EFK Stack and Services ==="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Check for duplicate services
echo "Checking for existing services..."
EXISTING_PIDS=$(ps aux | grep -E "python.*(user-service|order-service|payment-service)/main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$EXISTING_PIDS" ]; then
    echo "Warning: Found existing service processes: $EXISTING_PIDS"
    echo "Killing existing processes..."
    kill $EXISTING_PIDS 2>/dev/null
    sleep 2
fi

# Check for services on ports
for port in 8001 8002 8003; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "Warning: Port $port is in use, killing process..."
        lsof -ti:$port | xargs kill 2>/dev/null
        sleep 1
    fi
done

# Check for Docker containers
EXISTING_CONTAINERS=$(docker ps -q -f name=elasticsearch -f name=kibana -f name=fluentd)
if [ ! -z "$EXISTING_CONTAINERS" ]; then
    echo "Warning: Found existing Docker containers, stopping them..."
    docker-compose down 2>/dev/null
    sleep 2
fi

# Create logs directory
mkdir -p logs

# Start EFK stack with Docker Compose
echo "Starting Elasticsearch, Kibana, and Fluentd..."
docker-compose up -d

echo "Waiting for Elasticsearch to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:9200 > /dev/null 2>&1; then
        echo "Elasticsearch is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Waiting... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "Error: Elasticsearch failed to start"
    exit 1
fi

echo "Waiting for Kibana to be ready..."
sleep 10

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start services in background
echo "Starting FastAPI services..."

# Start User Service
echo "Starting User Service on port 8001..."
python3 services/user-service/main.py > logs/user-service.log 2>&1 &
USER_PID=$!

sleep 2

# Start Order Service
echo "Starting Order Service on port 8002..."
python3 services/order-service/main.py > logs/order-service.log 2>&1 &
ORDER_PID=$!

sleep 2

# Start Payment Service
echo "Starting Payment Service on port 8003..."
python3 services/payment-service/main.py > logs/payment-service.log 2>&1 &
PAYMENT_PID=$!

sleep 3

# Verify services are running
echo "Verifying services..."
for port in 8001 8002 8003; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✓ Service on port $port is healthy"
    else
        echo "✗ Service on port $port is not responding"
    fi
done

# Save PIDs
echo "$USER_PID" > .user_service.pid
echo "$ORDER_PID" > .order_service.pid
echo "$PAYMENT_PID" > .payment_service.pid

echo ""
echo "=== EFK Stack Started Successfully ==="
echo ""
echo "Services:"
echo "  User Service:     http://localhost:8001"
echo "  Order Service:    http://localhost:8002"
echo "  Payment Service:  http://localhost:8003"
echo "  Elasticsearch:    http://localhost:9200"
echo "  Kibana:           http://localhost:5601"
echo ""
echo "To generate load: python3 scripts/load_generator.py"
echo "To start anomaly detector: python3 anomaly-detector/detector.py"
echo "To view monitoring UI: cd monitoring-ui/src && python3 -m http.server 3000"
echo "To run tests: pytest tests/test_services.py -v"
echo "To stop: ./stop.sh"
echo ""