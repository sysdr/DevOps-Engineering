#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "============================================"
echo "Starting Local Development Environment"
echo "============================================"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r services/order-service/requirements.txt
pip install -r tests/requirements.txt

# Start OpenTelemetry Collector (requires Docker for collector)
echo "Starting infrastructure (Collector, Jaeger, Prometheus)..."
docker-compose up -d otel-collector jaeger prometheus

# Wait for infrastructure
sleep 10

# Start services in background
echo "Starting microservices..."

cd services/order-service
uvicorn main:app --host 0.0.0.0 --port 8000 &
ORDER_PID=$!
cd ../..

cd services/inventory-service
uvicorn main:app --host 0.0.0.0 --port 8001 &
INVENTORY_PID=$!
cd ../..

cd services/payment-service
uvicorn main:app --host 0.0.0.0 --port 8002 &
PAYMENT_PID=$!
cd ../..

# Save PIDs
echo "$ORDER_PID $INVENTORY_PID $PAYMENT_PID" > .local-pids

echo ""
echo "Local services started!"
echo "PIDs saved to .local-pids"
echo ""
echo "Services:"
echo "  • Order Service:     http://localhost:8000"
echo "  • Inventory Service: http://localhost:8001"
echo "  • Payment Service:   http://localhost:8002"
echo ""
echo "Observability:"
echo "  • Jaeger UI:         http://localhost:16686"
echo "  • Prometheus:        http://localhost:9090"
echo ""
echo "Stop with: ./stop-local.sh"
