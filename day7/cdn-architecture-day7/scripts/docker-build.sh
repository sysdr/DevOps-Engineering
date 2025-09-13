#!/bin/bash

echo "🐳 Building CDN Architecture Docker Images..."

# Build backend image
docker build -f docker/Dockerfile.backend -t cdn-backend:latest .

# Build frontend image  
docker build -f docker/Dockerfile.frontend -t cdn-frontend:latest .

echo "✅ Docker images built successfully!"
echo "🚀 To start with Docker: docker-compose up -d"
