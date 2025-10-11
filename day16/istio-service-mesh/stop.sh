#!/bin/bash

GREEN='\033[0;32m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log "🛑 Stopping Istio Service Mesh Demo..."

# Kill port forwarding
pkill -f "kubectl port-forward" || true

# Delete Kind cluster
kind delete cluster --name istio-demo || true

# Deactivate virtual environment
deactivate 2>/dev/null || true

log "✅ Cleanup complete!"
