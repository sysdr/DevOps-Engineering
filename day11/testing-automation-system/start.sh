#!/bin/bash

echo "🚀 Starting Testing Automation System..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies for frontend
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Start backend API in background
echo "🔧 Starting backend API..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait for API to start
sleep 5

# Start frontend in background
echo "🌐 Starting frontend dashboard..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Store PIDs for cleanup
echo $API_PID > api.pid
echo $FRONTEND_PID > frontend.pid

echo "✅ System started!"
echo "🔗 API: http://localhost:8000"
echo "🔗 Dashboard: http://localhost:3000"
echo "📊 API Docs: http://localhost:8000/docs"

# Run initial tests
echo "🧪 Running initial test suite..."
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v

# Run performance test
echo "⚡ Running performance test..."
k6 run k6/load-test.js

echo "🎉 Testing Automation System is ready!"
echo "Run 'bash stop.sh' to stop all services"
