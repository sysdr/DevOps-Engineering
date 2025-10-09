#!/bin/bash

echo "🛑 Stopping WebApp Operator..."

if kubectl cluster-info &>/dev/null; then
    echo "🎯 Cleaning up Kubernetes resources..."
    
    # Delete WebApps (this will trigger operator cleanup)
    kubectl delete webapps --all || true
    
    # Delete operator
    kubectl delete -f k8s-manifests/operator-deployment.yaml || true
    
    # Delete RBAC and CRDs
    kubectl delete -f k8s-manifests/rbac.yaml || true
    kubectl delete -f k8s-manifests/resource-quota.yaml || true
    kubectl delete -f k8s-manifests/webapp-crd.yaml || true
    
    # Kill port forwarding
    pkill -f "kubectl port-forward" || true
    
    echo "✅ Kubernetes cleanup complete!"
    
else
    echo "📦 Stopping Docker Compose..."
    docker-compose down
    
    echo "✅ Docker cleanup complete!"
fi

echo "🏁 WebApp Operator stopped!"
