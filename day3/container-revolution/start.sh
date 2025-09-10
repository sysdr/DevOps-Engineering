#!/bin/bash

# Set project directory and Python command
PROJECT_DIR="$(pwd)"
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Python 3 not found. Please install Python 3.11 or later."
    exit 1
fi

echo "🚀 Starting Container Revolution Platform"

# Check if running in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "📝 Activating virtual environment"
    source venv/bin/activate
fi

# Check and install Podman if needed
if ! command -v podman &> /dev/null; then
    echo "📦 Installing Podman"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y podman
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install podman
    fi
fi

# Check and install Trivy if needed
if ! command -v trivy &> /dev/null; then
    echo "🔍 Installing Trivy"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
        echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
        sudo apt-get update && sudo apt-get install -y trivy
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install trivy
    fi
fi

# Update Trivy database
echo "📊 Updating Trivy vulnerability database"
trivy image --download-db-only

# Start backend server
echo "🖥️  Starting backend server on port 5000"
cd "${PROJECT_DIR}/src/backend/api"
$PYTHON_CMD app.py &
BACKEND_PID=$!
cd "${PROJECT_DIR}"

# Start frontend server
echo "🌐 Starting frontend server on port 8080"
cd "${PROJECT_DIR}/src/frontend"
$PYTHON_CMD -m http.server 8080 &
FRONTEND_PID=$!
cd "${PROJECT_DIR}"

# Save PIDs for cleanup
mkdir -p logs
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo "✅ Platform started successfully!"
echo "🌐 Frontend: http://localhost:8080"
echo "🔌 Backend API: http://localhost:5000"
echo "📊 Health Check: http://localhost:5000/api/health"

# Build demo container
echo "🔨 Building demo container with Podman"
podman build -t demo-app:amd64 -f "${PROJECT_DIR}/src/containers/Dockerfile" "${PROJECT_DIR}"

echo "🎉 Container Revolution Platform is ready!"
echo "Run './stop.sh' to stop all services"
