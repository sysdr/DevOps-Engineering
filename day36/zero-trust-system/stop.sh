#!/bin/bash
echo "Stopping Zero-Trust Architecture Demo..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/logs/auth.pid" ]; then
    kill $(cat "$SCRIPT_DIR/logs/auth.pid") 2>/dev/null
    rm "$SCRIPT_DIR/logs/auth.pid"
fi

if [ -f "$SCRIPT_DIR/logs/policy.pid" ]; then
    kill $(cat "$SCRIPT_DIR/logs/policy.pid") 2>/dev/null
    rm "$SCRIPT_DIR/logs/policy.pid"
fi

if [ -f "$SCRIPT_DIR/logs/resource.pid" ]; then
    kill $(cat "$SCRIPT_DIR/logs/resource.pid") 2>/dev/null
    rm "$SCRIPT_DIR/logs/resource.pid"
fi

if [ -f "$SCRIPT_DIR/logs/certs.pid" ]; then
    kill $(cat "$SCRIPT_DIR/logs/certs.pid") 2>/dev/null
    rm "$SCRIPT_DIR/logs/certs.pid"
fi

if [ -f "$SCRIPT_DIR/logs/frontend.pid" ]; then
    kill $(cat "$SCRIPT_DIR/logs/frontend.pid") 2>/dev/null
    rm "$SCRIPT_DIR/logs/frontend.pid"
fi

# Kill any remaining processes
pkill -f "python main.py"
pkill -f "react-scripts"

echo "All services stopped."
