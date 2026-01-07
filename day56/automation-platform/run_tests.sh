#!/bin/bash

echo "=== Running Test Suite ==="

source venv/bin/activate

# Set PYTHONPATH to include current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Running unit tests..."
pytest tests/ -v --cov=backend --cov-report=term-missing

echo ""
echo "=== Test Summary ==="
echo "Coverage report generated"
