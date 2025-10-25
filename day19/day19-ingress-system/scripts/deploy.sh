#!/bin/bash

echo "🚀 Deploying Ingress Demo Application..."

# Build Docker images
echo "📦 Building Docker images..."
docker build -t day19-backend:latest ./backend
docker build -t day19-frontend:latest ./frontend

# Load images into kind cluster (if using kind)
if command -v kind &> /dev/null; then
    echo "📥 Loading images into kind cluster..."
    kind load docker-image day19-backend:latest
    kind load docker-image day19-frontend:latest
fi

# Apply Kubernetes manifests
echo "⚙️ Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/cert-manager.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f monitoring/prometheus.yaml

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/redis -n ingress-demo
kubectl wait --for=condition=available --timeout=300s deployment/backend -n ingress-demo
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n ingress-demo

echo "✅ Deployment complete!"

# Show status
echo "📊 Deployment Status:"
kubectl get pods -n ingress-demo
kubectl get services -n ingress-demo
kubectl get ingress -n ingress-demo

# Setup port forwarding for testing
echo "🌐 Setting up port forwarding..."
echo "Access the application at: http://localhost:8080"
kubectl port-forward -n ingress-demo service/frontend-service 8080:80 &

# Show logs
echo "📝 Recent logs:"
kubectl logs -n ingress-demo deployment/backend --tail=10
