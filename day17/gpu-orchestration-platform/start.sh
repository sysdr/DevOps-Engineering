#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/venv"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verify Python 3.11 is available
check_python() {
    if ! command_exists python3.11; then
        error "Python 3.11 is required but not installed"
    fi
    log "✅ Python 3.11 found"
}

# Setup virtual environment
setup_venv() {
    if [[ ! -d "${VENV_PATH}" ]]; then
        log "Creating Python virtual environment..."
        python3.11 -m venv "${VENV_PATH}"
    fi
    
    source "${VENV_PATH}/bin/activate"
    log "✅ Virtual environment activated"
    
    log "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    log "✅ Dependencies installed"
}

# Run tests
run_tests() {
    log "Running unit tests..."
    python -m pytest tests/unit/ -v --tb=short
    
    log "Running integration tests..."
    python -m pytest tests/integration/ -v --tb=short
    
    log "✅ All tests passed"
}

# Build Docker image (optional)
build_docker() {
    if command_exists docker; then
        log "Building Docker image..."
        docker build -t gpu-orchestration-platform .
        log "✅ Docker image built successfully"
    else
        warn "Docker not found, skipping image build"
    fi
}

# Start the application
start_application() {
    log "Starting GPU Orchestration Platform..."
    
    # Set Python path
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
    
    # Start the FastAPI server
    python -m uvicorn src.api.main:app \
        --host 0.0.0.0 \
        --port 8080 \
        --reload \
        --log-level info \
        --workers 1
}

# Verify application is running
verify_application() {
    log "Verifying application startup..."
    
    # Wait for server to start
    sleep 5
    
    if command_exists curl; then
        if curl -f http://localhost:8080/api/gpu/resources >/dev/null 2>&1; then
            log "✅ Application is running and responding"
            log "🚀 Dashboard available at: http://localhost:8080"
            log "📊 API endpoints available at: http://localhost:8080/docs"
        else
            warn "Application may not be fully ready yet"
        fi
    else
        warn "curl not available for health check"
        log "🚀 Application should be available at: http://localhost:8080"
    fi
}

# Main execution flow
main() {
    cd "${PROJECT_ROOT}"
    
    log "Starting GPU Orchestration Platform setup..."
    
    check_python
    setup_venv
    run_tests
    build_docker
    
    log "🎯 Starting application..."
    start_application &
    APP_PID=$!
    
    # Give the app time to start
    sleep 3
    verify_application
    
    log "🎉 GPU Orchestration Platform is now running!"
    log ""
    log "Available endpoints:"
    log "  • Dashboard: http://localhost:8080"
    log "  • API Docs: http://localhost:8080/docs"
    log "  • GPU Resources: http://localhost:8080/api/gpu/resources"
    log "  • Monitoring: http://localhost:8080/api/monitoring/metrics"
    log "  • Cost Analysis: http://localhost:8080/api/costs/analysis"
    log ""
    log "Press Ctrl+C to stop the application"
    
    # Wait for the application process
    wait $APP_PID
}

# Handle interrupts gracefully
trap 'log "Shutting down..."; kill $APP_PID 2>/dev/null; exit 0' INT TERM

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
