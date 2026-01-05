#!/bin/bash

set -e

echo "=========================================="
echo "Starting AI DevOps Platform"
echo "=========================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Start backend services
echo "Starting backend services..."
cd services

# Start Code Analyzer
echo "Starting Code Analyzer on port 8001..."
cd code-analyzer
uvicorn app.main:app --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &
CODE_ANALYZER_PID=$!
cd ..

# Start Log Analyzer
echo "Starting Log Analyzer on port 8002..."
cd log-analyzer
uvicorn app.main:app --host 0.0.0.0 --port 8002 > /dev/null 2>&1 &
LOG_ANALYZER_PID=$!
cd ..

# Start Incident Manager
echo "Starting Incident Manager on port 8003..."
cd incident-manager
uvicorn app.main:app --host 0.0.0.0 --port 8003 > /dev/null 2>&1 &
INCIDENT_MANAGER_PID=$!
cd ..

# Start Doc Generator
echo "Starting Doc Generator on port 8004..."
cd doc-generator
uvicorn app.main:app --host 0.0.0.0 --port 8004 > /dev/null 2>&1 &
DOC_GENERATOR_PID=$!
cd ..

cd ..

# Wait for services to start
echo "Waiting for services to be ready..."
sleep 5

# Check health of all services
echo "Checking service health..."
for port in 8001 8002 8003 8004; do
    if curl -s http://localhost:$port/health > /dev/null; then
        echo "✓ Service on port $port is healthy"
    else
        echo "✗ Service on port $port is not responding"
    fi
done

# Start frontend
echo "Starting frontend on port 3000..."
cd frontend

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install > /dev/null 2>&1
fi

BROWSER=none npm start > /dev/null 2>&1 &
FRONTEND_PID=$!

cd ..

# Save PIDs
echo $CODE_ANALYZER_PID > .code_analyzer.pid
echo $LOG_ANALYZER_PID > .log_analyzer.pid
echo $INCIDENT_MANAGER_PID > .incident_manager.pid
echo $DOC_GENERATOR_PID > .doc_generator.pid
echo $FRONTEND_PID > .frontend.pid

echo "=========================================="
echo "✅ AI DevOps Platform is running!"
echo "=========================================="
echo ""
echo "Access the dashboard at: http://localhost:3000"
echo ""
echo "API Endpoints:"
echo "  - Code Analyzer:     http://localhost:8001/docs"
echo "  - Log Analyzer:      http://localhost:8002/docs"
echo "  - Incident Manager:  http://localhost:8003/docs"
echo "  - Doc Generator:     http://localhost:8004/docs"
echo ""
echo "Run './stop.sh' to stop all services"
echo "=========================================="
