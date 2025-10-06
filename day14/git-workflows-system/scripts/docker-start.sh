#!/bin/bash

echo "🐳 Starting Git Workflows Manager with Docker"

# Build and start services
docker-compose up --build -d

echo "✅ Services started with Docker!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"

# Show logs
docker-compose logs -f
