#!/bin/bash

# DevOps Foundation Day 1 - Start Script
set -e

PROJECT_NAME="devops-day1-foundation"
PYTHON_VERSION="3.11"

echo "🚀 Starting DevOps Foundation Day 1 Infrastructure..."

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found. Installing..."
    # Add installation commands based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update && sudo apt install -y python3.11 python3.11-venv python3.11-dev
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python@3.11
    fi
fi

# Create and activate virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Start backend server
echo "🖥️ Starting backend server..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Start frontend development server
echo "🌐 Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Save PIDs for stop script
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo "✅ All services started successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🖥️ Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 To stop all services, run: ./stop.sh"

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v

echo "🎉 DevOps Foundation Day 1 is ready!"
