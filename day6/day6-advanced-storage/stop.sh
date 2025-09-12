#!/bin/bash

echo "🛑 Stopping Advanced Storage & Database Patterns Application"

# Stop Python application
pkill -f "python src/main.py" || true

# Stop Docker services
echo "🐳 Stopping Docker services..."
docker-compose down

# Deactivate virtual environment
deactivate 2>/dev/null || true

echo "✅ Application stopped successfully!"
