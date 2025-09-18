#!/bin/bash
echo "🚀 Starting Artifact Security System..."

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
cd frontend
npm install
cd ..

# Start Harbor registry
echo "Starting Harbor registry..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for registry to be ready
echo "Waiting for registry to be ready..."
sleep 30

# Start backend
echo "Starting backend API..."
cd backend
python app/main.py &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting frontend dashboard..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ System started successfully!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API: http://localhost:8000"
echo "📦 Registry: http://localhost:8080"

# Store PIDs for stop script
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

wait
