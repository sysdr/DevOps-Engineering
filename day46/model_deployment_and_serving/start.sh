#!/bin/bash

echo "Starting Model Serving Platform..."

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate

# Install Python dependencies
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start Redis
echo "Starting Redis..."
if ! pgrep redis-server > /dev/null; then
    redis-server --daemonize yes --port 6379
    sleep 2
fi

# Start backend
echo "Starting backend service..."
cd backend
python -m uvicorn model_service:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

# Install frontend dependencies and start
echo "Starting frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
sleep 5

echo ""
echo "==================================="
echo "Model Serving Platform is running!"
echo "==================================="
echo ""
echo "Dashboard: http://localhost:3000"
echo "API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Metrics: http://localhost:8000/metrics"
echo ""
echo "Run demo: python scripts/demo.py"
echo "Load test: python scripts/load_test.py"
echo ""
echo "Stop services: ./stop.sh"
echo ""
