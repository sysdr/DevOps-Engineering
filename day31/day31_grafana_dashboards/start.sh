#!/bin/bash

echo "=========================================="
echo "Starting Grafana Dashboard System"
echo "=========================================="

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install pytest requests

# Start metrics service
echo "Starting metrics service on port 8000..."
cd backend
python metrics_service.py &
METRICS_PID=$!
cd ..

sleep 3

# Start dashboard API
echo "Starting dashboard API on port 8001..."
cd backend
python dashboard_api.py &
API_PID=$!
cd ..

sleep 3

# Start Grafana with Docker
echo "Starting Grafana with Docker Compose..."
docker-compose up -d grafana

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Install frontend dependencies and start
echo "Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/react-scripts" ]; then
    echo "Installing npm packages..."
    npm install
fi

echo "Starting React frontend on port 3001..."
PORT=3001 WDS_SOCKET_HOST=localhost WDS_SOCKET_PORT=3001 npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "Services Started Successfully!"
echo "=========================================="
echo "Metrics Service:    http://localhost:8000"
echo "Dashboard API:      http://localhost:8001"
echo "Grafana UI:         http://localhost:3000 (admin/admin)"
echo "React Frontend:     http://localhost:3001"
echo ""
echo "Running tests in 15 seconds..."
sleep 15

# Run tests
echo ""
echo "Running automated tests..."
pytest tests/ -v

echo ""
echo "=========================================="
echo "System is ready!"
echo "=========================================="
echo "Open http://localhost:3001 for the management UI"
echo "Open http://localhost:3000 for Grafana (admin/admin)"
echo ""
echo "Process IDs:"
echo "Metrics PID: $METRICS_PID"
echo "API PID: $API_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop all services, run: ./stop.sh"

# Save PIDs
echo $METRICS_PID > .metrics.pid
echo $API_PID > .api.pid
echo $FRONTEND_PID > .frontend.pid

wait
