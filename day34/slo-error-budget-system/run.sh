#!/bin/bash

echo "========================================"
echo "Running SLO & Error Budget System Tests"
echo "========================================"

# Install test dependencies
echo "Installing test dependencies..."
pip3 install pytest pytest-asyncio httpx --break-system-packages

# Run tests
echo "Running tests..."
python3 -m pytest tests/ -v

echo ""
echo "Tests completed!"
