#!/bin/bash

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Starting Python Services Only ==="

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

# Create logs directory
mkdir -p logs

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Start services in background
echo "Starting FastAPI services..."

# Start User Service
echo "Starting User Service on port 8001..."
cd "$SCRIPT_DIR"
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
echo "=== Services Started Successfully ==="
echo ""
echo "Services:"
echo "  User Service:     http://localhost:8001"
echo "  Order Service:    http://localhost:8002"
echo "  Payment Service:  http://localhost:8003"
echo ""
echo "To generate load: python3 scripts/load_generator.py"
echo "To run tests: pytest tests/test_services.py -v"
echo "To stop: ./stop-services.sh"
echo ""

