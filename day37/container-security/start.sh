#!/bin/bash

echo "Starting Container Security Platform..."

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 not found. Using default python3..."
    PYTHON_CMD=python3
else
    PYTHON_CMD=python3.11
fi

# Create and activate virtual environment for scanner
echo "Setting up Scanner service..."
cd scanner
$PYTHON_CMD -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python app/main.py &
SCANNER_PID=$!
deactivate
cd ..

# Create and activate virtual environment for runtime monitor
echo "Setting up Runtime Monitor service..."
cd runtime-monitor
$PYTHON_CMD -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python app/main.py &
MONITOR_PID=$!
deactivate
cd ..

# Create and activate virtual environment for admission controller
echo "Setting up Admission Controller service..."
cd admission-controller
$PYTHON_CMD -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python app/main.py &
ADMISSION_PID=$!
deactivate
cd ..

# Create and activate virtual environment for benchmark
echo "Setting up Benchmark service..."
cd benchmark
$PYTHON_CMD -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python app/main.py &
BENCHMARK_PID=$!
deactivate
cd ..

# Setup and start dashboard
echo "Setting up Dashboard..."
cd dashboard
if [ ! -d "node_modules" ]; then
    npm install > /dev/null 2>&1
fi
PORT=3000 npm start &
DASHBOARD_PID=$!
cd ..

# Save PIDs
echo $SCANNER_PID > scanner.pid
echo $MONITOR_PID > monitor.pid
echo $ADMISSION_PID > admission.pid
echo $BENCHMARK_PID > benchmark.pid
echo $DASHBOARD_PID > dashboard.pid

echo ""
echo "============================================"
echo "Container Security Platform Started!"
echo "============================================"
echo "Scanner API:      http://localhost:8001"
echo "Runtime Monitor:  http://localhost:8002"
echo "Admission Ctrl:   http://localhost:8003"
echo "Benchmark API:    http://localhost:8004"
echo "Dashboard:        http://localhost:3000"
echo "============================================"
echo ""
echo "Services are starting... Wait 30 seconds for full initialization"
echo "Press Ctrl+C to stop (or run ./stop.sh)"
echo ""

wait
