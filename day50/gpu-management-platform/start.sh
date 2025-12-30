#!/bin/bash

set -e

echo "=== Starting GPU Management Platform ==="

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install --upgrade pip --quiet
pip install -r mig-controller/requirements.txt --quiet
pip install -r gpu-scheduler/requirements.txt --quiet
pip install -r cost-optimizer/requirements.txt --quiet

# Install test dependencies
pip install -r tests/requirements.txt --quiet

# Start backend services
echo "Starting MIG Controller..."
python mig-controller/app/main.py &
MIG_PID=$!
sleep 3

echo "Starting GPU Scheduler..."
python gpu-scheduler/app/main.py &
SCHEDULER_PID=$!
sleep 3

echo "Starting Cost Optimizer..."
python cost-optimizer/app/main.py &
COST_PID=$!
sleep 3

echo "Backend services started!"
echo "  - MIG Controller: http://localhost:8001"
echo "  - GPU Scheduler: http://localhost:8002"
echo "  - Cost Optimizer: http://localhost:8003"

# Setup and start dashboard
echo "Setting up React dashboard..."
cd dashboard

if [ ! -d "node_modules" ]; then
    echo "Installing dashboard dependencies..."
    npm install --silent
fi

echo "Starting dashboard..."
BROWSER=none npm start &
DASHBOARD_PID=$!

cd ..

# Save PIDs
echo $MIG_PID > .mig.pid
echo $SCHEDULER_PID > .scheduler.pid
echo $COST_PID > .cost.pid
echo $DASHBOARD_PID > .dashboard.pid

echo ""
echo "=== All services started! ==="
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 MIG Controller API: http://localhost:8001/docs"
echo "📅 GPU Scheduler API: http://localhost:8002/docs"
echo "💰 Cost Optimizer API: http://localhost:8003/docs"
echo ""
echo "Run './stop.sh' to stop all services"
echo ""

# Wait and run tests
sleep 10
echo "Running integration tests..."
python -m pytest tests/test_integration.py -v

# Demonstrate functionality
echo ""
echo "=== Demonstrating GPU Management ==="
echo ""

# Configure MIG on GPU 0
echo "1. Enabling MIG on GPU 0..."
curl -s -X POST http://localhost:8001/gpu/0/mig/enable | python -m json.tool

echo ""
echo "2. Configuring MIG instances..."
curl -s -X POST http://localhost:8001/gpu/0/mig/configure \
  -H "Content-Type: application/json" \
  -d '{"gpu_id": 0, "profiles": [{"profile": "1g.5gb", "instances": 3}]}' \
  | python -m json.tool

echo ""
echo "3. Scheduling a small training job..."
curl -s -X POST http://localhost:8002/schedule \
  -H "Content-Type: application/json" \
  -d '{"job_id": "training-job-1", "memory_required": 4096, "can_use_spot": false}' \
  | python -m json.tool

echo ""
echo "4. Getting cost analytics..."
curl -s http://localhost:8003/analytics | python -m json.tool

echo ""
echo "5. Viewing cluster state..."
curl -s http://localhost:8002/cluster/state | python -m json.tool

echo ""
echo "=== Demo Complete! ==="
echo "Open http://localhost:3000 to see the dashboard"
echo ""

wait
