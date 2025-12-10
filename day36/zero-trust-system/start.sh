#!/bin/bash
echo "Starting Zero-Trust Architecture Demo..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if running in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Start backend services
echo "Starting Auth Service..."
cd "$SCRIPT_DIR/auth-service" && python main.py > "$SCRIPT_DIR/logs/auth.log" 2>&1 &
AUTH_PID=$!
cd "$SCRIPT_DIR"

echo "Starting Policy Service..."
cd "$SCRIPT_DIR/policy-service" && python main.py > "$SCRIPT_DIR/logs/policy.log" 2>&1 &
POLICY_PID=$!
cd "$SCRIPT_DIR"

echo "Starting Resource Service..."
cd "$SCRIPT_DIR/resource-service" && python main.py > "$SCRIPT_DIR/logs/resource.log" 2>&1 &
RESOURCE_PID=$!
cd "$SCRIPT_DIR"

echo "Starting Certificate Service..."
cd "$SCRIPT_DIR/certs" && python main.py > "$SCRIPT_DIR/logs/certs.log" 2>&1 &
CERT_PID=$!
cd "$SCRIPT_DIR"

# Wait for backend services to start
echo "Waiting for backend services to initialize..."
sleep 5

# Start frontend
echo "Starting Frontend Dashboard..."
cd "$SCRIPT_DIR/frontend" && PORT=3000 npm start > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# Save PIDs
echo $AUTH_PID > "$SCRIPT_DIR/logs/auth.pid"
echo $POLICY_PID > "$SCRIPT_DIR/logs/policy.pid"
echo $RESOURCE_PID > "$SCRIPT_DIR/logs/resource.pid"
echo $CERT_PID > "$SCRIPT_DIR/logs/certs.pid"
echo $FRONTEND_PID > "$SCRIPT_DIR/logs/frontend.pid"

echo ""
echo "=========================================="
echo "Zero-Trust Architecture Demo Started!"
echo "=========================================="
echo "Auth Service:     http://localhost:8001"
echo "Policy Service:   http://localhost:8003"
echo "Resource Service: http://localhost:8002"
echo "Cert Service:     http://localhost:8004"
echo "Dashboard:        http://localhost:3000"
echo "=========================================="
echo ""
echo "View logs in the logs/ directory"
echo "Run ./stop.sh to stop all services"
