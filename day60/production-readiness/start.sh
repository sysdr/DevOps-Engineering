#!/bin/bash

echo "Starting Production Readiness Platform..."

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Start backend
echo "Starting backend service..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
sleep 5

# Install and start frontend
echo "Starting frontend..."
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================="
echo "Production Readiness Platform Started!"
echo "=================================="
echo "Backend API: http://localhost:8000"
echo "Frontend Dashboard: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo "Metrics: http://localhost:8000/metrics"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Save PIDs
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

wait
