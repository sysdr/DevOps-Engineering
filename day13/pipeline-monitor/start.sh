#!/bin/bash

echo "🚀 Starting Pipeline Performance Monitor..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Start Redis in background (if not running)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🔴 Starting Redis server..."
    redis-server --daemonize yes --port 6379
fi

# Start backend server in background
echo "🐍 Starting Backend API server..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# Start frontend server in background
echo "⚛️ Starting Frontend React server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Store PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo "✅ All services started!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"

# Wait for user input to stop
read -p "Press Enter to stop all services..."

# Kill processes
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi

echo "🛑 All services stopped"
