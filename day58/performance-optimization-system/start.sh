#!/bin/bash

echo "========================================="
echo "Starting Performance Optimization System"
echo "========================================="

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt

# Start backend
echo "Starting backend API..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Start frontend
echo "Starting frontend..."
cd frontend
python -m http.server 3000 &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================="
echo "✅ System Started Successfully!"
echo "========================================="
echo ""
echo "🌐 API: http://localhost:8000"
echo "🎨 Dashboard: http://localhost:3000"
echo "📊 Health: http://localhost:8000/health"
echo ""
echo "API Endpoints:"
echo "  - Performance Profile: http://localhost:8000/api/profiler/flame-graph"
echo "  - Auto-scaling Status: http://localhost:8000/api/autoscaler/status"
echo "  - Scaling Events: http://localhost:8000/api/autoscaler/events"
echo "  - Query Recommendations: http://localhost:8000/api/optimizer/recommendations"
echo "  - Capacity Runway: http://localhost:8000/api/capacity/runway"
echo ""
echo "Test Commands:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/api/autoscaler/status"
echo "  curl http://localhost:8000/api/autoscaler/events"
echo "  curl http://localhost:8000/api/optimizer/recommendations"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Save PIDs
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for processes
wait
