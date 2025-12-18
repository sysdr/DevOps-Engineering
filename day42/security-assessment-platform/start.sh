#!/bin/bash

echo "=== Starting Security Assessment Platform ==="

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt --quiet
cd ..

# Start backend
echo "Starting FastAPI backend..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
done

# Install frontend dependencies and start
if [ -d "frontend" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install --silent
    fi
    
    echo "Starting React frontend..."
    PORT=3000 npm start &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo "=== Security Assessment Platform Started ==="
    echo "Backend API: http://localhost:8000"
    echo "Frontend Dashboard: http://localhost:3000"
    echo "API Documentation: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Store PIDs for cleanup
    echo $BACKEND_PID > .backend.pid
    echo $FRONTEND_PID > .frontend.pid
    
    # Wait for interrupt
    wait $BACKEND_PID $FRONTEND_PID
else
    echo ""
    echo "=== Backend Started ==="
    echo "API: http://localhost:8000"
    echo "Documentation: http://localhost:8000/docs"
    echo ""
    echo "PID: $BACKEND_PID"
    echo $BACKEND_PID > .backend.pid
    wait $BACKEND_PID
fi
