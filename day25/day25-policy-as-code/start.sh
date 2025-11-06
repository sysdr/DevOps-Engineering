#!/bin/bash

echo "========================================="
echo "Starting Policy as Code Dashboard"
echo "========================================="

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3.11 -m venv venv
    cd ..
fi

# Activate virtual environment and install dependencies
echo "Installing backend dependencies..."
cd backend
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
cd ..

# Start backend server
echo "Starting backend server on http://localhost:5000..."
cd backend
source venv/bin/activate
python src/api/server.py > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 3

# Start frontend server
echo "Starting frontend server on http://localhost:3000..."
cd frontend/public
python3 -m http.server 3000 > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../../frontend.pid
cd ../..

echo
echo "========================================="
echo "✓ All services started successfully!"
echo "========================================="
echo
echo "Access the dashboard:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:5000"
echo "  API Health: http://localhost:5000/health"
echo
echo "Logs:"
echo "  Backend: tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
echo
echo "To stop: ./stop.sh"
echo "========================================="
echo

# Run tests
echo "Running tests..."
cd backend
source venv/bin/activate
pytest ../tests/test_policies.py -v
cd ..

echo
echo "Dashboard is ready! Open http://localhost:3000 in your browser"
