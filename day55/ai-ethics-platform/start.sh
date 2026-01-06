#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting AI Ethics & Governance Platform..."
echo "Working directory: $SCRIPT_DIR"

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv || python3.11 -m venv venv || python3.10 -m venv venv
fi
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
for service in services/*/; do
    if [ -f "$service/requirements.txt" ]; then
        echo "Installing dependencies for $service"
        pip install -r "$service/requirements.txt"
    fi
done

# Install test dependencies
if [ -f "tests/requirements.txt" ]; then
    pip install -r tests/requirements.txt
fi

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d postgres redis

# Wait for databases
echo "Waiting for databases..."
sleep 5

# Start backend services
echo "Starting backend services..."
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/ai_ethics"
export REDIS_HOST="localhost"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Start services from their directories with proper paths
cd "$SCRIPT_DIR/services/bias-detection"
python src/main.py > "$SCRIPT_DIR/logs/bias-detection.log" 2>&1 &
BIAS_PID=$!
echo "Bias Detection Service started (PID: $BIAS_PID)"

cd "$SCRIPT_DIR/services/fairness-monitor"
python src/main.py > "$SCRIPT_DIR/logs/fairness-monitor.log" 2>&1 &
FAIRNESS_PID=$!
echo "Fairness Monitor Service started (PID: $FAIRNESS_PID)"

cd "$SCRIPT_DIR/services/explainability"
python src/main.py > "$SCRIPT_DIR/logs/explainability.log" 2>&1 &
EXPLAIN_PID=$!
echo "Explainability Service started (PID: $EXPLAIN_PID)"

cd "$SCRIPT_DIR/services/governance"
python src/main.py > "$SCRIPT_DIR/logs/governance.log" 2>&1 &
GOVERNANCE_PID=$!
echo "Governance Service started (PID: $GOVERNANCE_PID)"

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check if services are running
for port in 8001 8002 8003 8004; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✓ Service on port $port is healthy"
    else
        echo "⚠ Service on port $port may not be ready yet"
    fi
done

# Start frontend
echo "Starting frontend..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi
BROWSER=none npm start > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

# Save PIDs for cleanup
echo "$BIAS_PID" > "$SCRIPT_DIR/logs/bias-detection.pid"
echo "$FAIRNESS_PID" > "$SCRIPT_DIR/logs/fairness-monitor.pid"
echo "$EXPLAIN_PID" > "$SCRIPT_DIR/logs/explainability.pid"
echo "$GOVERNANCE_PID" > "$SCRIPT_DIR/logs/governance.pid"
echo "$FRONTEND_PID" > "$SCRIPT_DIR/logs/frontend.pid"

echo "
================================================
AI Ethics & Governance Platform Started!
================================================

Services:
- Bias Detection API: http://localhost:8001
- Fairness Monitor API: http://localhost:8002
- Explainability API: http://localhost:8003
- Governance API: http://localhost:8004
- Dashboard: http://localhost:3000

PIDs saved in logs/ directory
Press Ctrl+C to stop all services
"

wait
