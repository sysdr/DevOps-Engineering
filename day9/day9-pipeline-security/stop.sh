#!/bin/bash

echo "🛑 Stopping DevSecOps Security Pipeline"
echo "======================================"

# Kill any running Python processes
pkill -f "python -m src.main" 2>/dev/null || true

# Stop Docker containers if running
docker-compose down 2>/dev/null || true

echo "✅ Security pipeline stopped"
