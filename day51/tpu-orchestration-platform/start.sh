#!/bin/bash

echo "Starting TPU Orchestration Platform..."

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Start backend
echo "Starting backend server..."
cd backend
PYTHONPATH=. python -m app.main &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✓ Backend is running"
else
    echo "✗ Backend failed to start"
    exit 1
fi

# Install and start frontend
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Starting frontend..."
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "TPU Orchestration Platform Started!"
echo "=========================================="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Save PIDs
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

# Wait for user interrupt
wait
