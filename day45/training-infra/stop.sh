#!/bin/bash

if [ -f .server.pid ]; then
    PID=$(cat .server.pid)
    echo "Stopping server (PID: $PID)..."
    kill $PID 2>/dev/null
    rm .server.pid
    echo "Server stopped"
else
    echo "No running server found"
fi
