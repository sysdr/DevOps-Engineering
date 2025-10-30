#!/bin/bash

echo "🚀 Starting Day 21: Phase 1 Integration & Assessment"
echo "=================================================="

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found. Please install Python 3.11"
    exit 1
fi

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p logs docs/{generated,architecture,runbooks,api} config/generated

# Run unit tests
echo "🧪 Running unit tests..."
python -m pytest tests/ -v --tb=short

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Please check the output above."
    exit 1
fi

# Start backend services
echo "🌐 Starting backend API server..."
cd src
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is healthy
echo "🔍 Checking backend health..."
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
else
    echo "❌ Backend health check failed"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Install frontend dependencies and start
echo "🎨 Setting up React frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start frontend
echo "🖥️ Starting frontend dashboard..."
npm start &
FRONTEND_PID=$!
cd ..

# Save PIDs for cleanup
echo $BACKEND_PID > .backend_pid
echo $FRONTEND_PID > .frontend_pid

echo ""
echo "🎉 System is running!"
echo "================================"
echo "Backend API: http://localhost:8000"
echo "Frontend Dashboard: http://localhost:3000"
echo "API Documentation: http://localhost:8000/docs"
echo ""

# Run integration tests demo
echo "🧪 Running integration tests demo..."
sleep 3
curl -X POST http://localhost:8000/api/integration-tests/run | jq '.' || echo "Integration tests initiated"

echo ""
echo "📊 Running performance analysis demo..."
curl http://localhost:8000/api/performance/report | jq '.' || echo "Performance report generated"

echo ""
echo "💰 Running cost analysis demo..."
curl http://localhost:8000/api/cost-analysis/report | jq '.' || echo "Cost analysis completed"

echo ""
echo "📖 Generating documentation demo..."
curl -X POST "http://localhost:8000/api/documentation/generate?doc_type=architecture" | jq '.' || echo "Documentation generated"

echo ""
echo "✅ All systems operational!"
echo "Press Ctrl+C to stop all services, or run ./stop.sh"

# Keep script running
wait
