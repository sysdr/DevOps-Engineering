#!/bin/bash

echo "🚀 Starting Git Workflows Manager"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment"
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "📥 Installing backend dependencies"
pip install -r backend/requirements.txt

# Install frontend dependencies
echo "📥 Installing frontend dependencies"
cd frontend
npm install
cd ..

# Start backend in background
echo "🔧 Starting backend server"
cd backend && python app/main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# Start frontend
echo "🎨 Starting frontend server"
cd frontend && npm start &
FRONTEND_PID=$!
cd ..

# Save PIDs for cleanup
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo "✅ Services started!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"

# Run tests
echo "🧪 Running tests"
source venv/bin/activate
cd backend && python -m pytest tests/ -v
cd ../frontend && npm test -- --watchAll=false
cd ..

echo "🎯 Demo ready! Visit http://localhost:3000"
echo "💡 Try the workflow actions in the dashboard"

# Wait for user input to stop
read -p "Press Enter to stop services..."

# Stop services
./stop.sh
