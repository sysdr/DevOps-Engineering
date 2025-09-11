#!/bin/bash

set -e

echo "🚀 Starting Kubernetes Production Dashboard"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run the main script first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "📦 Installing frontend dependencies..."
cd src/frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

echo "🏗️ Building frontend..."
npm run build

echo "🚀 Starting backend..."
cd ../../
export FLASK_ENV=development
export PYTHONPATH=$PWD/src/backend:$PYTHONPATH
python src/backend/app.py &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"
echo $BACKEND_PID > backend.pid

# Wait for backend to start
sleep 5

echo "🌐 Starting frontend development server..."
cd src/frontend
REACT_APP_API_BASE=http://localhost:5000 npm start &
FRONTEND_PID=$!

echo "Frontend started with PID: $FRONTEND_PID"
echo $FRONTEND_PID > ../../frontend.pid

cd ../../

echo "✅ Dashboard is starting up..."
echo "📊 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:5000"
echo "📈 Metrics: http://localhost:5000/metrics"
echo ""
echo "🛑 To stop the services, run: bash stop.sh"
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Test if services are running
echo "🔍 Checking service health..."
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend not accessible yet (may still be starting)"
fi

echo ""
echo "🎉 Services are starting! Check the URLs above."
echo "⏰ Frontend may take a few more seconds to fully load."
