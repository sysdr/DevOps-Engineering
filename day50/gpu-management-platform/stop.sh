#!/bin/bash

echo "Stopping GPU Management Platform..."

# Kill processes
if [ -f .mig.pid ]; then
    kill $(cat .mig.pid) 2>/dev/null || true
    rm .mig.pid
fi

if [ -f .scheduler.pid ]; then
    kill $(cat .scheduler.pid) 2>/dev/null || true
    rm .scheduler.pid
fi

if [ -f .cost.pid ]; then
    kill $(cat .cost.pid) 2>/dev/null || true
    rm .cost.pid
fi

if [ -f .dashboard.pid ]; then
    kill $(cat .dashboard.pid) 2>/dev/null || true
    rm .dashboard.pid
fi

# Kill any remaining processes on our ports
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:8002 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

echo "All services stopped!"
