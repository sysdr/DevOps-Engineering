#!/bin/bash

echo "Stopping GitOps Observability Platform..."

if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null || true
    rm backend.pid
fi

if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null || true
    rm frontend.pid
fi

# Kill any remaining processes
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

echo "Platform stopped."
