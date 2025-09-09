#!/bin/bash

echo "🚀 Starting OpenTofu Infrastructure Manager"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Python 3.11 is available
print_step "Checking Python version..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" == "3.11" ]]; then
        PYTHON_CMD=python3
    else
        echo "⚠️  Python 3.11 not found. Using available Python 3.x"
        PYTHON_CMD=python3
    fi
else
    echo "❌ Python 3 not found. Please install Python 3.11"
    exit 1
fi

print_status "Using Python: $PYTHON_CMD"

# Create and activate virtual environment
print_step "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# Install backend dependencies
print_step "Installing backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Install frontend dependencies
print_step "Installing frontend dependencies..."
cd frontend
if command -v npm &> /dev/null; then
    npm install
    print_status "Frontend dependencies installed"
else
    echo "⚠️  npm not found. Please install Node.js and npm"
    echo "Frontend will not be available without npm"
fi
cd ..

# Start backend
print_step "Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend if npm is available
if command -v npm &> /dev/null; then
    print_step "Starting frontend server..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend to start
    sleep 5
fi

# Run tests
print_step "Running integration tests..."
cd tests
python test_api.py
if command -v npm &> /dev/null; then
    python test_frontend.py
fi
cd ..

print_status "🎉 OpenTofu Infrastructure Manager is running!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop the application, run: ./stop.sh"

# Save PIDs for stop script
echo $BACKEND_PID > .backend.pid
if [ ! -z "$FRONTEND_PID" ]; then
    echo $FRONTEND_PID > .frontend.pid
fi

# Keep script running
wait
