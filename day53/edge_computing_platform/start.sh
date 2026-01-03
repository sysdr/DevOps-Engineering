#!/bin/bash

set -e

echo "Starting Edge Computing Platform..."

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -q -r requirements.txt
cd ..

# Install edge agent dependencies
echo "Installing edge agent dependencies..."
cd edge_agent
pip install -q -r requirements.txt
cd ..

# Start backend
echo "Starting control plane..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

sleep 5

# Start edge agents
echo "Starting edge agents..."
cd edge_agent
python main.py datacenter &
AGENT1_PID=$!
sleep 2
python main.py factory &
AGENT2_PID=$!
sleep 2
python main.py mobile &
AGENT3_PID=$!
cd ..

# Save PIDs
echo $BACKEND_PID > /tmp/edge_backend.pid
echo $AGENT1_PID > /tmp/edge_agent1.pid
echo $AGENT2_PID > /tmp/edge_agent2.pid
echo $AGENT3_PID > /tmp/edge_agent3.pid

echo ""
echo "✅ Edge Computing Platform started!"
echo ""
echo "Access points:"
echo "  Dashboard: http://localhost:8000/index.html (copy from frontend/public/)"
echo "  API: http://localhost:8000/api"
echo "  Health: http://localhost:8000/health"
echo ""
echo "To stop: ./stop.sh"
