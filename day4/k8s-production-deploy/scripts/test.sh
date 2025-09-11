#!/bin/bash

set -e

echo "🧪 Running Kubernetes Production Dashboard Tests"
echo "=============================================="

# Activate virtual environment
source venv/bin/activate

echo "🔍 Running linting..."
flake8 src/backend/ --max-line-length=100 --exclude=__pycache__

echo "🔒 Running security scan..."
bandit -r src/backend/ -f json -o security-report.json
safety check

echo "🧪 Running unit tests..."
python -m pytest tests/test_backend.py -v --cov=src/backend --cov-report=html

echo "🔗 Running integration tests..."
python -m pytest tests/test_integration.py -v

echo "✅ All tests passed!"
