#!/bin/bash
# Deploy to Kubernetes

echo "☸️  Deploying to Kubernetes..."

# Build Docker image
docker build -t wasm-edge-platform:latest .

# Apply Kubernetes manifests
kubectl apply -k k8s/base/

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/wasm-edge-api -n wasm-edge-platform

# Get service URL
kubectl get service wasm-edge-api-service -n wasm-edge-platform

echo "✅ Deployment complete"
echo "Use 'kubectl port-forward service/wasm-edge-api-service 8000:80 -n wasm-edge-platform' to access locally"
