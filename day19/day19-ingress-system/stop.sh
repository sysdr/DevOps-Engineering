#!/bin/bash

echo "🛑 Stopping Day 19: Ingress & Load Balancing System"
echo "================================================="

# Stop background processes
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🛑 Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
    fi
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🛑 Stopping frontend server (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
    fi
    rm .frontend.pid
fi

# Kill any remaining processes
pkill -f "uvicorn.*main:app"
pkill -f "python3.*http.server.*3000"
pkill -f "locust"

# Stop Kubernetes port forwarding
pkill -f "kubectl port-forward"

echo "✅ All processes stopped"

# Clean up Kubernetes resources (optional)
read -p "🗑️ Do you want to clean up Kubernetes resources? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl delete namespace ingress-demo
    echo "✅ Kubernetes resources cleaned up"
fi

echo "🏁 Cleanup complete!"
