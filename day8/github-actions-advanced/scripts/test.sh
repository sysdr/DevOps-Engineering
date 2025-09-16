#!/bin/bash
set -e

echo "🧪 Running all tests..."

# Test API service
echo "Testing API service..."
cd api-service
python -m pytest tests/ -v --cov=src
cd ..

# Test User service
echo "Testing User service..." 
cd user-service
python -m pytest tests/ -v --cov=src
cd ..

# Test Frontend
echo "Testing Frontend..."
cd frontend
npm test -- --coverage --watchAll=false
cd ..

echo "✅ All tests passed!"
