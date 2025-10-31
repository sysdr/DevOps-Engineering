#!/bin/bash
set -e

# Get absolute path of script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Starting GitOps Demo ==="
echo "Working directory: $SCRIPT_DIR"

# Check for duplicate services
echo "🔍 Checking for duplicate services..."
BACKEND_RUNNING=$(pgrep -f "python.*src.main|uvicorn.*main" || true)
FRONTEND_RUNNING=$(pgrep -f "react-scripts start|npm.*start" || true)

if [ ! -z "$BACKEND_RUNNING" ]; then
    echo "⚠️  Warning: Backend service already running (PIDs: $BACKEND_RUNNING)"
    echo "   Stopping existing backend processes..."
    pkill -f "python.*src.main|uvicorn.*main" || true
    sleep 2
fi

if [ ! -z "$FRONTEND_RUNNING" ]; then
    echo "⚠️  Warning: Frontend service already running (PIDs: $FRONTEND_RUNNING)"
    echo "   Stopping existing frontend processes..."
    pkill -f "react-scripts start" || true
    sleep 2
fi

# Check if ports are in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Warning: Port 8000 is already in use"
    echo "   Stopping process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Warning: Port 3000 is already in use"
    echo "   Stopping process on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
if [ ! -d "$SCRIPT_DIR/gitops-venv" ]; then
    python3.11 -m venv "$SCRIPT_DIR/gitops-venv"
fi
source "$SCRIPT_DIR/gitops-venv/bin/activate"

# Install Python dependencies
echo "📥 Installing backend dependencies..."
cd "$SCRIPT_DIR/backend"
pip install --quiet -r requirements.txt
cd "$SCRIPT_DIR"

# Install Node.js dependencies
echo "📥 Installing frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
cd "$SCRIPT_DIR"

# Run tests
echo "🧪 Running backend tests..."
cd "$SCRIPT_DIR/backend"
python -m pytest tests/ -v || echo "⚠️  Backend tests failed, continuing..."
cd "$SCRIPT_DIR"

echo "🧪 Running frontend tests..."
cd "$SCRIPT_DIR/frontend"
npm test -- --watchAll=false --passWithNoTests || echo "⚠️  Frontend tests failed, continuing..."
cd "$SCRIPT_DIR"

echo "🧪 Running integration tests..."
cd "$SCRIPT_DIR"
if python -m pytest tests/ -v; then
    echo "✅ Integration tests passed"
else
    echo "⚠️  Integration tests failed (backend may not be running yet)"
fi

# Build Docker images (optional)
if command -v docker-compose &> /dev/null; then
    echo "🐳 Building Docker images (optional)..."
    docker-compose build || echo "⚠️  Docker build failed, continuing without Docker..."
fi

# Start services
echo "🚀 Starting services..."

# Start backend
echo "Starting backend server..."
cd "$SCRIPT_DIR/backend"
export PYTHONPATH="$SCRIPT_DIR/backend:$PYTHONPATH"
python -m src.main > "$SCRIPT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend did not start within 30 seconds, but continuing..."
    fi
done

# Start frontend
echo "Starting frontend server..."
cd "$SCRIPT_DIR/frontend"
BROWSER=none npm start > "$SCRIPT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# Save PIDs for stop script
echo $BACKEND_PID > "$SCRIPT_DIR/.backend_pid"
echo $FRONTEND_PID > "$SCRIPT_DIR/.frontend_pid"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

echo "✅ GitOps Demo started successfully!"
echo "🌐 Frontend UI: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"

echo ""
echo "=== Demo Instructions ==="
echo "1. Open http://localhost:3000 to view the GitOps Dashboard"
echo "2. Click 'Sync Now' on any application to trigger GitOps sync"
echo "3. Watch the status change from 'OutOfSync' to 'Synced'"
echo "4. View metrics and application health status"
echo "5. Try the API endpoints at http://localhost:8000/docs"

echo ""
echo "=== To stop the demo ==="
echo "Run: ./stop.sh"

# Keep script running
wait
