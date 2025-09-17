#!/bin/bash

echo "🚀 Starting DevSecOps Security Pipeline"
echo "====================================="

# Activate virtual environment
source venv/bin/activate

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --cov=src

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi

# Start the application
echo "🌐 Starting security dashboard..."
echo "Dashboard available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
