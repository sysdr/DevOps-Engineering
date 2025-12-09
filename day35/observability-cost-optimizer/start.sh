#!/bin/bash

echo "=================================="
echo "Observability Cost Optimizer Setup"
echo "=================================="

# Resolve project root to handle relative paths
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Create and prepare virtual environment (fallback to virtualenv if needed)
echo "Creating Python virtual environment..."
VENV_DIR="$PROJECT_ROOT/venv"
if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3.11 -m venv "$VENV_DIR" 2>/dev/null || python3 -m venv "$VENV_DIR" || python3 -m virtualenv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

echo "Installing Python dependencies..."
"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install -r requirements.txt

# Kill any existing processes on ports 8000 and 3000
echo "Cleaning up any existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend
echo "Starting backend server..."
cd "$PROJECT_ROOT/backend"
"$VENV_DIR/bin/uvicorn" main:app --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/backend.log" 2>&1 &
BACKEND_PID=$!
cd "$PROJECT_ROOT"

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..10}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  sleep 1
done

# Install frontend dependencies and start
echo "Setting up frontend..."
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/react-scripts" ]; then
  echo "Installing frontend dependencies..."
  npm install --legacy-peer-deps
fi

# Use npx to ensure react-scripts is found, or use the full path
BROWSER=none npx react-scripts start > "$PROJECT_ROOT/frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"

echo ""
echo "=================================="
echo "✅ Application Started Successfully!"
echo "=================================="
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================="

# Save PIDs for stop script
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for Ctrl+C
wait
