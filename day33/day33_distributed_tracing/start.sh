#!/bin/bash

echo "=== Starting Day 33 Distributed Tracing System ==="

# Create and activate virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start Jaeger (using Docker)
echo "Starting Jaeger..."
docker run -d --name jaeger \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14269:14269 \
  -p 9411:9411 \
  jaegertracing/all-in-one:1.51

echo "Waiting for Jaeger to start..."
sleep 5

# Start services
echo "Starting Order Service..."
python order_service/main.py &
ORDER_PID=$!
sleep 3

echo "Starting Inventory Service..."
python inventory_service/main.py &
INVENTORY_PID=$!
sleep 3

echo "Starting Payment Service..."
python payment_service/main.py &
PAYMENT_PID=$!
sleep 3

echo "Starting APM Dashboard Backend..."
python apm_dashboard/apm_api.py &
APM_PID=$!
sleep 3

# Install and start React dashboard
echo "Setting up React APM Dashboard..."
(cd apm_dashboard && npm install && echo "Starting React Dashboard..." && BROWSER=none npm start &)
REACT_PID=$!

sleep 5

# Run tests
echo ""
echo "=== Running Tests ==="
pytest tests/ -v

# Generate sample traffic
echo ""
echo "=== Generating Sample Traffic ==="
sleep 3

for i in {1..10}; do
  echo "Sending request $i..."
  curl -X POST http://localhost:8001/orders \
    -H "Content-Type: application/json" \
    -d '{
      "customer_id": "CUST-'$i'",
      "items": [
        {"product_id": "PROD-001", "quantity": 2, "price": 49.99},
        {"product_id": "PROD-002", "quantity": 1, "price": 99.99}
      ]
    }' 2>/dev/null
  sleep 1
done

echo ""
echo "=== System Running ==="
echo "✓ Order Service: http://localhost:8001"
echo "✓ Inventory Service: http://localhost:8002"
echo "✓ Payment Service: http://localhost:8003"
echo "✓ Jaeger UI: http://localhost:16686"
echo "✓ APM Dashboard: http://localhost:3000"
echo "✓ APM API: http://localhost:8000"
echo ""
echo "View traces in Jaeger UI and metrics in APM Dashboard"
echo "Press Ctrl+C to stop all services"
echo ""

# Save PIDs for cleanup
echo $ORDER_PID > .pids
echo $INVENTORY_PID >> .pids
echo $PAYMENT_PID >> .pids
echo $APM_PID >> .pids
echo $REACT_PID >> .pids

wait
