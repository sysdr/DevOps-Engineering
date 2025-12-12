#!/bin/bash
# Complete setup, verification, and testing script

set -e

PROJECT_DIR="$(pwd)/secrets-management-system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Complete Setup and Verification ==="

# Step 1: Run setup.sh if needed
cd "$SCRIPT_DIR"
if [ ! -d "$PROJECT_DIR" ] || [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Running setup.sh..."
    bash setup.sh
else
    echo "Project directory exists, checking files..."
fi

# Step 2: Verify all required files exist
cd "$PROJECT_DIR"
echo ""
echo "=== Verifying Required Files ==="
required_files=(
    "requirements.txt"
    "backend/main.py"
    "frontend/src/App.jsx"
    "frontend/src/index.jsx"
    "frontend/package.json"
    "frontend/vite.config.js"
    "frontend/index.html"
    "tests/test_secrets.py"
    "k8s/vault-deployment.yaml"
    "k8s/external-secrets-operator.yaml"
    "k8s/cert-manager.yaml"
    "docker/Dockerfile.backend"
    "docker/Dockerfile.frontend"
    "docker/.dockerignore"
    "docker/docker-compose.yml"
    "start.sh"
    "stop.sh"
    "scripts/demo.sh"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "✗ MISSING: $file"
        missing_files+=("$file")
    else
        echo "✓ $file"
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "ERROR: Missing ${#missing_files[@]} required files!"
    echo "Re-running setup.sh..."
    cd "$SCRIPT_DIR"
    bash setup.sh
    exit 1
fi

echo ""
echo "✓ All required files exist!"

# Step 3: Check for running services and stop them
echo ""
echo "=== Checking for Running Services ==="
if pgrep -f "uvicorn backend.main:app" > /dev/null; then
    echo "Stopping existing backend processes..."
    pkill -f "uvicorn backend.main:app" || true
    sleep 2
fi

if pgrep -f "vite" > /dev/null; then
    echo "Stopping existing frontend processes..."
    pkill -f "vite" || true
    sleep 2
fi

# Step 4: Run tests
echo ""
echo "=== Running Tests ==="
cd "$PROJECT_DIR"
if [ -d "venv" ]; then
    source venv/bin/activate
    python -m pytest tests/ -v || echo "WARNING: Some tests failed"
else
    echo "ERROR: Virtual environment not found!"
    exit 1
fi

# Step 5: Start services
echo ""
echo "=== Starting Services ==="
cd "$PROJECT_DIR"

# Check if start.sh exists and is executable
if [ -f "start.sh" ] && [ -x "start.sh" ]; then
    echo "Starting services using start.sh..."
    bash start.sh &
    START_PID=$!
    echo "Start script PID: $START_PID"
    sleep 5
    
    # Wait a bit for services to start
    sleep 3
else
    echo "ERROR: start.sh not found or not executable!"
    exit 1
fi

# Step 6: Check for duplicate services
echo ""
echo "=== Checking for Duplicate Services ==="
backend_count=$(pgrep -f "uvicorn backend.main:app" | wc -l)
frontend_count=$(pgrep -f "vite" | wc -l)

echo "Backend processes: $backend_count"
echo "Frontend processes: $frontend_count"

if [ "$backend_count" -gt 1 ]; then
    echo "WARNING: Multiple backend processes detected!"
    pkill -f "uvicorn backend.main:app"
    sleep 2
    echo "Starting single backend..."
    cd "$PROJECT_DIR"
    source venv/bin/activate
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
fi

if [ "$frontend_count" -gt 1 ]; then
    echo "WARNING: Multiple frontend processes detected!"
    pkill -f "vite"
    sleep 2
fi

# Step 7: Wait for services to be ready
echo ""
echo "=== Waiting for Services to Start ==="
max_attempts=30
attempt=0
backend_ready=false
frontend_ready=false

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        backend_ready=true
        echo "✓ Backend is ready"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done

if [ "$backend_ready" = false ]; then
    echo "ERROR: Backend failed to start!"
    exit 1
fi

attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        frontend_ready=true
        echo "✓ Frontend is ready"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done

# Step 8: Validate dashboard and metrics
echo ""
echo "=== Validating Dashboard and Metrics ==="

# Test API endpoints
echo "Testing API endpoints..."
stats_response=$(curl -s http://localhost:8000/stats)
if [ -n "$stats_response" ]; then
    echo "✓ Stats endpoint working"
    echo "$stats_response" | head -20
else
    echo "✗ Stats endpoint failed"
fi

# Test demo script
if [ -f "scripts/demo.sh" ] && [ -x "scripts/demo.sh" ]; then
    echo ""
    echo "Running demo script..."
    bash scripts/demo.sh || echo "WARNING: Demo script had issues"
fi

echo ""
echo "=== Setup Complete ==="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"

