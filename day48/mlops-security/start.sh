#!/bin/bash

set -e

echo "Starting MLOps Security & Governance Platform..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Start backend
echo "Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
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
BROWSER=none npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================================="
echo "✅ MLOps Security & Governance Platform Started!"
echo "=================================================="
echo ""
echo "🔒 Backend API: http://localhost:8000"
echo "📊 Dashboard: http://localhost:3000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Save PIDs to file
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for both processes
wait
