#!/bin/bash
set -e

echo "🚀 Starting Day 8: GitHub Actions Advanced Patterns Implementation"

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies for services
echo "📦 Installing API service dependencies..."
cd api-service
pip install -r requirements.txt
cd ..

echo "📦 Installing User service dependencies..."
cd user-service  
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📦 Installing Frontend dependencies..."
cd frontend
npm install
cd ..

# Build all services
echo "🔨 Building services..."
chmod +x scripts/build.sh
./scripts/build.sh

# Run tests
echo "🧪 Running tests..."
chmod +x scripts/test.sh
./scripts/test.sh

# Start services with Docker Compose
echo "🚀 Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Health checks
echo "🔍 Running health checks..."
curl -f http://localhost:8000/health || echo "❌ API service not ready"
curl -f http://localhost:8001/health || echo "❌ User service not ready"

echo ""
echo "🎉 Day 8 Implementation Complete!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API Service: http://localhost:8000"
echo "👥 User Service: http://localhost:8001"
echo ""
echo "🔍 Verify the following:"
echo "✅ Matrix builds configured for parallel testing"
echo "✅ Reusable workflows for consistent CI/CD"
echo "✅ Advanced caching strategies implemented"
echo "✅ OIDC authentication configured"
echo "✅ Multi-environment deployment patterns"
echo "✅ Composite actions for deployment logic"
echo ""
echo "📝 Next: Run 'docker-compose logs -f' to view logs"
echo "📝 Stop: Run './stop.sh' to stop all services"
