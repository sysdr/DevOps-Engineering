#!/bin/bash

# DevOps Foundation Day 1 - Docker Start Script
echo "🐳 Starting DevOps Foundation with Docker..."

# Build and start services
docker-compose up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

# Show logs
echo "📋 Service logs:"
docker-compose logs --tail=20

echo "✅ Docker services started successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🖥️ Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 To stop Docker services, run: docker-compose down"
