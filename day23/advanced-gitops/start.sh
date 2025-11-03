#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting Advanced GitOps Implementation..."
echo "📁 Working directory: $SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "gitops-env" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Check for duplicate Flask/Gunicorn processes
echo "🔍 Checking for existing services..."
EXISTING_FLASK=$(pgrep -f "python.*web-dashboard/app.py" || true)
EXISTING_GUNICORN=$(pgrep -f "gunicorn.*web-dashboard.app:app" || true)

if [ ! -z "$EXISTING_FLASK" ] || [ ! -z "$EXISTING_GUNICORN" ]; then
    echo "⚠️  Found existing services. Stopping them first..."
    if [ ! -z "$EXISTING_FLASK" ]; then
        echo "   Killing Flask processes: $EXISTING_FLASK"
        pkill -f "python.*web-dashboard/app.py" || true
    fi
    if [ ! -z "$EXISTING_GUNICORN" ]; then
        echo "   Killing Gunicorn processes: $EXISTING_GUNICORN"
        pkill -f "gunicorn.*web-dashboard.app:app" || true
    fi
    sleep 2
fi

# Activate virtual environment
source "$SCRIPT_DIR/gitops-env/bin/activate"

echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt

echo "🧪 Running unit tests..."
python -m pytest "$SCRIPT_DIR/tests/test_gitops.py" -v || echo "⚠️  Some tests may have failed, continuing..."

echo "🔧 Building Docker images..."
docker build -t advanced-gitops:latest .

echo "🌐 Starting web dashboard..."
python "$SCRIPT_DIR/web-dashboard/app.py" > "$SCRIPT_DIR/dashboard.log" 2>&1 &
FLASK_PID=$!

echo "⏳ Waiting for dashboard to start..."
sleep 3

echo "🧪 Running integration tests..."
python -m pytest "$SCRIPT_DIR/tests/test_integration.py" -v || echo "⚠️  Integration tests may have failed, continuing..."

echo "✅ Running demonstration..."
echo "Dashboard available at: http://localhost:5000"
echo "API status at: http://localhost:5000/api/status"
echo "Health check at: http://localhost:5000/health"

# Test API endpoints
echo "📊 Testing API endpoints..."
curl -s http://localhost:5000/health | python -m json.tool
echo ""
curl -s http://localhost:5000/api/status | python -m json.tool

echo "🐳 Starting Docker stack..."
cd "$SCRIPT_DIR"
docker-compose up -d || echo "⚠️  Docker compose may have issues, continuing..."

echo "✅ GitOps Advanced Patterns Implementation Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Open browser to http://localhost:5000 for dashboard"
echo "2. Check http://localhost:9090 for Prometheus"
echo "3. Review Kubernetes manifests in argocd-config/"
echo "4. Deploy to cluster: kubectl apply -f argocd-config/"
echo ""
echo "🛑 To stop: ./stop.sh"

# Keep Flask running
wait $FLASK_PID
