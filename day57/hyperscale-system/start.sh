#!/bin/bash

echo "Starting Hyperscale Architecture System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start backend
echo "Starting backend server..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 3

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install --silent
    cd ..
fi

# Start frontend
echo "Starting frontend dashboard..."
cd frontend
PORT=3000 npm start &
FRONTEND_PID=$!
cd ..

# Save PIDs
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "=================================="
echo "✅ Hyperscale System Started!"
echo "=================================="
echo ""
echo "🔹 Backend API: http://localhost:8000"
echo "🔹 API Docs: http://localhost:8000/docs"
echo "🔹 Dashboard: http://localhost:3000"
echo "🔹 Metrics: http://localhost:8000/metrics"
echo ""
echo "To stop: ./stop.sh"
echo ""

# Keep script running
wait
