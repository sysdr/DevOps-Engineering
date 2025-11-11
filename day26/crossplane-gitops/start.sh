#!/bin/bash

echo "Starting Crossplane Infrastructure Platform..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

# Start API server
echo "Starting API server in demo mode..."
export DEMO_MODE=true
python backend/crossplane_api.py &
API_PID=$!

# Start frontend web server
echo "Starting frontend web server..."
# Kill any existing server on port 8080
pkill -f "python3 -m http.server 8080" 2>/dev/null
sleep 1

cd frontend
python3 -m http.server 8080 --bind 0.0.0.0 > /tmp/frontend_server.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 2

# Verify server started
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "Frontend server started successfully (PID: $FRONTEND_PID)"
    # Test if server is responding
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo "Frontend server is responding on http://localhost:8080"
    else
        echo "Warning: Server started but may not be fully ready yet"
    fi
else
    echo "Error: Frontend server failed to start. Check /tmp/frontend_server.log:"
    tail -5 /tmp/frontend_server.log 2>/dev/null || echo "Log file not found"
    FRONTEND_PID=""
fi

# Get WSL IP if in WSL
WSL_IP=""
if [ -f /proc/version ] && grep -qi microsoft /proc/version; then
    WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null)
    if [ -z "$WSL_IP" ]; then
        WSL_IP=$(ip addr show eth0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
    fi
fi

echo "API server started with PID: $API_PID"
echo "Frontend server started with PID: $FRONTEND_PID"
echo ""
echo "API: http://localhost:8000"
if [ -n "$WSL_IP" ]; then
    echo "API (WSL): http://$WSL_IP:8000"
fi
echo "Dashboard: http://localhost:8080"
if [ -n "$WSL_IP" ]; then
    echo "Dashboard (WSL): http://$WSL_IP:8080"
fi
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "To stop: ./stop.sh"
echo ""
echo "PID: $API_PID" > .api.pid
if [ -n "$FRONTEND_PID" ]; then
    echo "PID: $FRONTEND_PID" > .frontend.pid
fi

# Wait a bit for servers to start
sleep 3

# Open dashboard in browser - try WSL IP first if available, otherwise localhost
if [ -n "$WSL_IP" ]; then
    DASHBOARD_URL="http://$WSL_IP:8080"
    echo "Opening dashboard at $DASHBOARD_URL (WSL IP)"
else
    DASHBOARD_URL="http://localhost:8080"
    echo "Opening dashboard at $DASHBOARD_URL"
fi

if command -v xdg-open > /dev/null; then
    xdg-open "$DASHBOARD_URL" 2>/dev/null &
elif command -v open > /dev/null; then
    open "$DASHBOARD_URL" 2>/dev/null &
fi

echo "System is running. Press Ctrl+C to view logs, or run ./stop.sh to stop."
tail -f /dev/null
