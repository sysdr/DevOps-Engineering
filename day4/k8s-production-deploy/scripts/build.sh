#!/bin/bash

set -e

echo "🏗️ Building Kubernetes Production Dashboard"
echo "=========================================="

# Build backend Docker image
echo "🐳 Building backend Docker image..."
docker build -f Dockerfile.backend -t k8s-dashboard-backend:latest .

# Build frontend Docker image
echo "🎨 Building frontend Docker image..."
docker build -f Dockerfile.frontend -t k8s-dashboard-frontend:latest .

echo "✅ Docker images built successfully"

# Run security scan
echo "🔒 Running security scan..."
if command -v trivy &> /dev/null; then
    trivy image k8s-dashboard-backend:latest
    trivy image k8s-dashboard-frontend:latest
else
    echo "⚠️ Trivy not installed, skipping security scan"
fi

echo "✅ Build completed successfully"
