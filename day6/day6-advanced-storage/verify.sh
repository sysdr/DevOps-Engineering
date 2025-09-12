#!/bin/bash

echo "🔍 Verifying Day 6 Implementation"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment created"
else
    echo "❌ Virtual environment missing"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if all required files exist
files_to_check=(
    "src/main.py"
    "src/backup.py"
    "frontend/index.html"
    "docker-compose.yml"
    "config/postgres/postgresql.conf"
    "config/pgbouncer/pgbouncer.ini"
    "tests/unit/test_database.py"
    "tests/integration/test_api.py"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Check if Docker services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Docker services running"
else
    echo "❌ Docker services not running"
fi

# Test API endpoints
echo "🧪 Testing API endpoints..."
curl -s http://localhost:8000/health > /dev/null && echo "✅ Health endpoint working" || echo "❌ Health endpoint failed"
curl -s http://localhost:8000/users > /dev/null && echo "✅ Users endpoint working" || echo "❌ Users endpoint failed"
curl -s http://localhost:8000/database/stats > /dev/null && echo "✅ Database stats endpoint working" || echo "❌ Database stats endpoint failed"

# Test dashboard
curl -s http://localhost:8000/dashboard > /dev/null && echo "✅ Dashboard accessible" || echo "❌ Dashboard not accessible"

echo "🎉 Verification complete!"
