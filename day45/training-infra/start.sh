#!/bin/bash

echo "Starting Training Infrastructure..."

# Activate virtual environment
source venv/bin/activate

# Start dashboard server
python -m src.dashboard &
SERVER_PID=$!

echo "Dashboard running at http://localhost:8000"
echo "Server PID: $SERVER_PID"
echo "Press Ctrl+C to stop"

# Save PID for stop script
echo $SERVER_PID > .server.pid

wait $SERVER_PID
