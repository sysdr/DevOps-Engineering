#!/bin/bash

echo "🔨 Building Day 21: Integration Assessment"
echo "========================================"

# Build backend
echo "🐍 Building backend..."
docker build -t day21-backend .

# Build frontend  
echo "⚛️ Building frontend..."
cd frontend
docker build -t day21-frontend .
cd ..

# Build with docker-compose
echo "🐳 Building with docker-compose..."
docker-compose build

echo "✅ Build completed!"
echo ""
echo "To run with Docker:"
echo "docker-compose up -d"
echo ""
echo "To run locally:"
echo "./start.sh"
