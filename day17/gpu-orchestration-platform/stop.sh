#!/bin/bash

set -euo pipefail

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log "Stopping GPU Orchestration Platform..."

# Kill any running Python processes on port 8080
if command -v lsof >/dev/null 2>&1; then
    PID=$(lsof -ti:8080 2>/dev/null || true)
    if [[ -n "$PID" ]]; then
        log "Killing process on port 8080 (PID: $PID)"
        kill -TERM $PID
        sleep 2
        # Force kill if still running
        if kill -0 $PID 2>/dev/null; then
            log "Force killing process $PID"
            kill -KILL $PID
        fi
    fi
fi

# Stop Docker containers if running
if command -v docker >/dev/null 2>&1; then
    if docker-compose ps -q >/dev/null 2>&1; then
        log "Stopping Docker containers..."
        docker-compose down
    fi
fi

log "✅ GPU Orchestration Platform stopped"
