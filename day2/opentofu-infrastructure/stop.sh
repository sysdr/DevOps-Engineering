#!/bin/bash

echo "🛑 Stopping OpenTofu Infrastructure Manager"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Kill backend process
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        print_status "Backend server stopped (PID: $BACKEND_PID)"
    else
        print_error "Backend process not found"
    fi
    rm .backend.pid
fi

# Kill frontend process
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        print_status "Frontend server stopped (PID: $FRONTEND_PID)"
    else
        print_error "Frontend process not found"
    fi
    rm .frontend.pid
fi

# Kill any remaining processes on ports 3000 and 8000
print_status "Cleaning up remaining processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Deactivate virtual environment if active
if [ "$VIRTUAL_ENV" != "" ]; then
    deactivate
    print_status "Virtual environment deactivated"
fi

print_status "✅ OpenTofu Infrastructure Manager stopped"
