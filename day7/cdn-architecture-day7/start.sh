#!/bin/bash

echo "🚀 Starting CDN Architecture System - Day 7"
echo "=============================================="

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found. Please install Python 3.11"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo "📦 Setting up Python virtual environment..."
cd backend
python3.11 -m venv venv
source venv/bin/activate

echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🧪 Running backend tests..."
python -m pytest tests/ -v

echo "🐍 Starting backend server..."
cd ..
nohup backend/venv/bin/python backend/src/main.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to start
sleep 5

echo "⚛️ Setting up React frontend..."
cd frontend
npm install

echo "🧪 Running frontend tests..."
npm test -- --coverage --watchAll=false

echo "🌐 Starting frontend development server..."
nohup npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

cd ..

# Save PIDs for stop script
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo ""
echo "🎉 CDN Architecture System is running!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8080"
echo ""
echo "📝 Available endpoints:"
echo "   POST /api/cdn/request - Simulate CDN request"
echo "   GET  /api/cdn/metrics - Get performance metrics"
echo "   POST /api/cdn/invalidate - Invalidate cache"
echo ""
echo "💡 Try the Request Simulator to see geographic routing!"
echo "📈 Check Analytics tab for performance insights"
echo "🔒 View Security tab for traffic filtering"
echo ""
echo "🛑 To stop: ./stop.sh"
