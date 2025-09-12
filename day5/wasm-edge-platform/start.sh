#!/bin/bash
# Start WASM Edge Computing Platform

set -e

echo "🚀 Starting WASM Edge Computing Platform"
echo "======================================="

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Build frontend
echo "⚛️  Building React frontend..."
cd frontend
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/react-scripts" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi
echo "🔨 Building React app..."
npm run build
cd ..

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Start the application
echo "🌐 Starting FastAPI server..."
echo "Platform will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
