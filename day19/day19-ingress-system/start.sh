#!/bin/bash

echo "🚀 Starting Day 19: Ingress & Load Balancing System"
echo "================================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found. Please install Python 3.11"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl"
    exit 1
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate
echo "✅ Virtual environment activated"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start local development server
echo "🚀 Starting backend server..."
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "🌐 Starting frontend server..."
cd frontend/src && python3 -m http.server 3000 &
FRONTEND_PID=$!

cd ../..

# Wait for servers to start
sleep 5

echo "✅ Servers started successfully!"
echo "🌐 Backend API: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo "📊 Metrics: http://localhost:8000/metrics"
echo "🏥 Health: http://localhost:8000/health"

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Start load test (optional)
echo "📈 Starting load test in background..."
locust -f tests/locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=60s --headless &

# Keep servers running
echo "🎯 System is running! Press Ctrl+C to stop."
echo "💡 Try these commands:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/api/ssl-info"
echo "   curl http://localhost:8000/metrics"

# Save PIDs for stop script
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

wait
