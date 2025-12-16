#!/bin/bash

echo "Starting Security Operations Center..."

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install --quiet -r backend/requirements.txt

# Start backend
echo "Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Install frontend dependencies and start
echo "Installing frontend dependencies..."
cd frontend
npm install --silent

echo "Starting frontend..."
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "Security Operations Center is running!"
echo "Backend API: http://localhost:8000"
echo "Frontend Dashboard: http://localhost:3000"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Save PIDs
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for Ctrl+C
wait
