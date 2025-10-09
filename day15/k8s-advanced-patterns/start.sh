#!/bin/bash

set -e

echo "🚀 Starting WebApp Operator Demo"

# Activate virtual environment
source venv/bin/activate

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Build Docker images
echo "🐳 Building Docker images..."
docker build -t webapp-operator:latest -f docker/Dockerfile.operator .
docker build -t webapp-dashboard:latest -f docker/Dockerfile.dashboard .

# Check if we're in a Kubernetes cluster
if kubectl cluster-info &>/dev/null; then
    echo "🎯 Deploying to Kubernetes..."
    
    # Apply CRDs and RBAC
    kubectl apply -f k8s-manifests/webapp-crd.yaml
    kubectl apply -f k8s-manifests/rbac.yaml
    kubectl apply -f k8s-manifests/resource-quota.yaml
    
    # Wait for CRD to be established
    echo "⏳ Waiting for CRD to be established..."
    kubectl wait --for condition=established --timeout=60s crd/webapps.platform.devops
    
    # Deploy operator
    kubectl apply -f k8s-manifests/operator-deployment.yaml
    
    # Wait for operator to be ready
    echo "⏳ Waiting for operator to be ready..."
    kubectl wait --for=condition=available --timeout=120s deployment/webapp-operator
    
    # Deploy sample WebApp
    kubectl apply -f k8s-manifests/sample-webapp.yaml
    
    # Show resources
    echo "📊 Current resources:"
    kubectl get webapps
    kubectl get deployments -l managed-by=webapp-operator
    kubectl get services -l managed-by=webapp-operator || true
    kubectl get pdb -l managed-by=webapp-operator || true
    
    # Port forward for metrics
    echo "🌐 Starting port forwarding..."
    kubectl port-forward service/webapp-operator-service 8000:8000 &
    
    echo "✅ Kubernetes deployment complete!"
    echo "📊 Operator metrics: http://localhost:8000/metrics"
    echo "🔍 Monitor WebApps: kubectl get webapps -w"
    
else
    echo "📦 Starting with Docker Compose..."
    docker-compose up -d
    
    echo "✅ Docker deployment complete!"
    echo "📊 Operator metrics: http://localhost:8000/metrics"
    echo "🌐 Dashboard: http://localhost:3000"
fi

echo ""
echo "🎉 WebApp Operator is running!"
echo ""
echo "Next steps:"
echo "1. View operator metrics at http://localhost:8000/metrics"
echo "2. Monitor operator logs: kubectl logs -f deployment/webapp-operator"
echo "3. Create/modify WebApps: kubectl apply -f k8s-manifests/sample-webapp.yaml"
echo "4. Scale WebApps: kubectl patch webapp demo-webapp -p '{\"spec\":{\"replicas\":5}}'"
