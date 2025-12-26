#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Model Monitoring Platform..."
echo "Working directory: $SCRIPT_DIR"

# Verify required files exist
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found in $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "backend/init_db.py" ]; then
    echo "❌ Error: backend/init_db.py not found"
    exit 1
fi

if [ ! -f "backend/generate_test_data.py" ]; then
    echo "❌ Error: backend/generate_test_data.py not found"
    exit 1
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || python3.11 -m venv venv || python -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start PostgreSQL in Docker
if ! docker ps | grep -q "monitoring-postgres"; then
    echo "Starting PostgreSQL in Docker..."
    # Remove any existing stopped container
    docker rm monitoring-postgres 2>/dev/null || true
    
    # Check if port 5432 is in use by another process
    if (lsof -i :5432 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q :5432) && ! docker ps | grep -q "monitoring-postgres"; then
        echo "⚠️  Port 5432 is in use. Attempting to use existing PostgreSQL..."
        echo "⚠️  If connection fails, please stop the existing PostgreSQL or configure it with password 'postgres'"
    else
        docker run -d --name monitoring-postgres \
            -e POSTGRES_PASSWORD=postgres \
            -e POSTGRES_DB=monitoring \
            -e POSTGRES_USER=postgres \
            -p 5433:5432 \
            postgres:15-alpine
        
        echo "Waiting for PostgreSQL to be ready..."
        for i in {1..30}; do
            if docker exec monitoring-postgres pg_isready -U postgres >/dev/null 2>&1; then
                echo "✓ PostgreSQL is ready"
                break
            fi
            if [ $i -eq 30 ]; then
                echo "⚠️  PostgreSQL may not be ready yet, continuing anyway..."
            fi
            sleep 1
        done
    fi
else
    echo "✓ PostgreSQL container already running"
fi

# Initialize database
echo "Initializing database..."
python "$SCRIPT_DIR/backend/init_db.py"

# Generate test data
echo "Generating test data..."
python "$SCRIPT_DIR/backend/generate_test_data.py"

# Start backend services
echo "Starting backend services..."
python "$SCRIPT_DIR/backend/metrics_collector/collector.py" &
python "$SCRIPT_DIR/backend/drift_detector/detector.py" &
python "$SCRIPT_DIR/backend/performance_tracker/tracker.py" &
python "$SCRIPT_DIR/backend/explainability/service.py" &
python "$SCRIPT_DIR/backend/fairness_monitor/monitor.py" &

# Start frontend
cd "$SCRIPT_DIR/frontend"
npm install
npm start &

echo "✅ Platform started!"
echo ""
echo "Access points:"
echo "  - Dashboard: http://localhost:3000"
echo "  - Metrics Collector: http://localhost:8000"
echo "  - Drift Detector: http://localhost:8001"
echo "  - Performance Tracker: http://localhost:8002"
echo "  - Explainability Service: http://localhost:8003"
echo "  - Fairness Monitor: http://localhost:8004"
