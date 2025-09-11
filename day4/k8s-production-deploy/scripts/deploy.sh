#!/bin/bash

set -e

echo "🚀 Deploying to Kubernetes"
echo "=========================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Apply Kubernetes manifests
echo "📦 Applying Kubernetes manifests..."

kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/rbac.yaml
kubectl apply -f k8s/base/backend-deployment.yaml
kubectl apply -f k8s/base/frontend-deployment.yaml
kubectl apply -f k8s/base/services.yaml
kubectl apply -f k8s/base/hpa.yaml

echo "🔒 Applying network policies..."
kubectl apply -f k8s/network-policies/

echo "⏰ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/k8s-dashboard-backend -n k8s-dashboard
kubectl wait --for=condition=available --timeout=300s deployment/k8s-dashboard-frontend -n k8s-dashboard

echo "🔍 Checking deployment status..."
kubectl get pods -n k8s-dashboard
kubectl get services -n k8s-dashboard

# Get LoadBalancer URL
FRONTEND_URL=$(kubectl get service k8s-dashboard-frontend-service -n k8s-dashboard -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
if [ -z "$FRONTEND_URL" ]; then
    FRONTEND_URL=$(kubectl get service k8s-dashboard-frontend-service -n k8s-dashboard -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
fi

if [ -n "$FRONTEND_URL" ]; then
    echo "🎉 Deployment successful!"
    echo "📊 Dashboard URL: http://$FRONTEND_URL"
else
    echo "⚠️ LoadBalancer URL not available yet. Check with:"
    echo "kubectl get services -n k8s-dashboard"
fi

echo "✅ Deployment completed"
