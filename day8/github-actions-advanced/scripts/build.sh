#!/bin/bash
set -e

echo "🔨 Building all services..."

# Build API service
echo "Building API service..."
cd api-service
docker build -f docker/Dockerfile -t api-service:latest .
cd ..

# Build User service  
echo "Building User service..."
cd user-service
docker build -f docker/Dockerfile -t user-service:latest .
cd ..

# Build Frontend
echo "Building Frontend..."
cd frontend
docker build -t frontend:latest .
cd ..

echo "✅ All services built successfully!"
