#!/bin/bash

echo "🐳 Starting CDN Architecture with Docker..."

# Start services
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🎉 CDN Architecture System is running with Docker!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8080"
echo ""
echo "📊 Check status: docker-compose ps"
echo "📋 View logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
