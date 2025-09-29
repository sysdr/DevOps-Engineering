#!/bin/bash

echo "🚀 Starting Multi-Environment Deployment Platform..."

# Activate virtual environment
source venv/bin/activate

# Install dependencies if not already installed
pip install -r backend/requirements.txt

echo "📋 Running tests..."
cd backend && python -m pytest tests/ -v
cd ..

echo "🐳 Building Docker images..."
cd infrastructure/docker
docker-compose build
docker-compose up -d redis

echo "🌐 Starting application..."
cd ../../
python backend/src/main.py &
APP_PID=$!

echo "✅ Application started!"
echo "📊 Dashboard available at: http://localhost:8000"
echo "🔗 API docs available at: http://localhost:8000/docs"
echo ""
echo "🔥 Demo Features:"
echo "  • Environment status monitoring"
echo "  • Blue-Green deployments"
echo "  • Canary deployments"
echo "  • Feature flag management"
echo "  • Real-time metrics"
echo ""
echo "Press Ctrl+C to stop..."

# Store PID for stop script
echo $APP_PID > app.pid

wait $APP_PID
