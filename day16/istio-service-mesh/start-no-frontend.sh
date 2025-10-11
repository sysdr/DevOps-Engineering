#!/bin/bash

set -e

PROJECT_NAME="istio-service-mesh"
PYTHON_VERSION="3.11"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log "🚀 Starting Istio Service Mesh Demo (No Frontend)..."

# Create and activate virtual environment
log "Creating Python virtual environment..."
python${PYTHON_VERSION} -m venv venv
source venv/bin/activate

# Install Python dependencies
log "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create Kind cluster
log "Creating Kubernetes cluster with Kind..."
kind create cluster --name istio-demo --config k8s/kind-config.yaml --wait 300s

# Install Istio
log "Installing Istio..."
if ! command -v istioctl &> /dev/null; then
    warn "Installing istioctl..."
    curl -sL https://istio.io/downloadIstio | sh -
    export PATH=$PWD/istio-*/bin:$PATH
    # Try to copy to /usr/local/bin, fallback to local directory
    if sudo cp istio-*/bin/istioctl /usr/local/bin/ 2>/dev/null; then
        log "istioctl installed to /usr/local/bin"
    else
        log "Installing istioctl to local directory (add to PATH manually)"
        mkdir -p ~/.local/bin
        cp istio-*/bin/istioctl ~/.local/bin/istioctl
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi

istioctl install --set values.defaultRevision=default -y
kubectl label namespace default istio-injection=enabled --overwrite

# Install observability addons
log "Installing observability stack..."
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.19/samples/addons/prometheus.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.19/samples/addons/grafana.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.19/samples/addons/jaeger.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.19/samples/addons/kiali.yaml

# Wait for Istio components
log "Waiting for Istio components to be ready..."
kubectl rollout status deployment/istiod -n istio-system --timeout=300s

# Build and load Docker images (excluding frontend)
log "Building Docker images..."
for service in user-service product-service order-service recommendation-service; do
    docker build -t ${service}:latest src/services/${service}/
    kind load docker-image ${service}:latest --name istio-demo
done

# Deploy applications
log "Deploying applications..."
kubectl apply -f k8s/manifests-no-frontend/

# Wait for application deployments (excluding frontend)
log "Waiting for applications to be ready..."
for service in user-service product-service order-service recommendation-service-v1 recommendation-service-v2; do
    kubectl rollout status deployment/${service} --timeout=300s
done

# Apply Istio configurations
log "Applying Istio configurations..."
kubectl apply -f k8s/istio/gateways/
kubectl apply -f k8s/istio/virtual-services/
kubectl apply -f k8s/istio/destination-rules/
kubectl apply -f k8s/istio/policies/

# Wait for configurations to propagate
log "Waiting for Istio configurations to propagate..."
sleep 30

# Port forward for access
log "Setting up port forwarding..."
kubectl port-forward service/istio-ingressgateway -n istio-system 8080:80 &
INGRESS_PID=$!

# Wait for services to be ready
log "Waiting for services to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost:8080/users > /dev/null 2>&1; then
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

log "✅ Istio Service Mesh is ready (No Frontend)!"
log ""
log "🌐 Access the services at:"
log "   Users: http://localhost:8080/users"
log "   Products: http://localhost:8080/products"
log "   Orders: http://localhost:8080/orders"
log "   Recommendations: http://localhost:8080/recommendations"
log ""
log "📊 Grafana dashboard: kubectl port-forward svc/grafana -n istio-system 3000:3000"
log "🔍 Jaeger tracing: kubectl port-forward svc/jaeger -n istio-system 16686:16686"
log "📈 Kiali dashboard: kubectl port-forward svc/kiali -n istio-system 20001:20001"
log ""
log "To run tests: python tests/test_services.py"
log "To stop: ./stop.sh"

# Keep port forwarding running
wait $INGRESS_PID
