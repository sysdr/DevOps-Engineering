#!/bin/bash

echo "Starting Supply Chain Security System..."

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
pip install -q pytest httpx

# Start backend
echo "Starting backend server..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend server..."
cd frontend
python3 -m http.server 3000 --directory public &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "Supply Chain Security System is running!"
echo "============================================"
echo "Backend API: http://localhost:8000"
echo "Dashboard: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Save PIDs
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

# Wait for interrupt
wait
