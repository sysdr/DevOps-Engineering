#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[DEMO] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[DEMO] $1${NC}"
}

log "🎬 Starting Istio Service Mesh Demo..."

# Test basic functionality
log "Testing basic service functionality..."
curl -s http://localhost:8080/users | jq '.[0]' || echo "Users service response"
curl -s http://localhost:8080/products | jq '.[0]' || echo "Products service response"

# Test canary deployment
log "Testing canary deployment (90% v1, 10% v2)..."
echo "Making 20 requests to recommendation service:"
for i in {1..20}; do
    version=$(curl -s http://localhost:8080/recommendations/1 | jq -r '.version')
    echo "Request $i: $version"
    sleep 0.5
done

# Test circuit breaker
log "Testing circuit breaker..."
echo "Making rapid requests to product service (some may fail intentionally):"
for i in {1..10}; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/products/1 || echo "FAILED")
    echo "Request $i: HTTP $status"
    sleep 0.2
done

# Show Istio configuration
log "Istio configuration summary:"
echo "Virtual Services:"
kubectl get virtualservices
echo ""
echo "Destination Rules:"
kubectl get destinationrules
echo ""
echo "Gateways:"
kubectl get gateways

# Show observability
log "Observability endpoints:"
info "📊 Grafana: kubectl port-forward svc/grafana -n istio-system 3000:3000"
info "🔍 Jaeger: kubectl port-forward svc/jaeger -n istio-system 16686:16686"
info "📈 Kiali: kubectl port-forward svc/kiali -n istio-system 20001:20001"
info "📊 Prometheus: kubectl port-forward svc/prometheus -n istio-system 9090:9090"

log "✅ Demo completed!"
log "🌐 Application is running at: http://localhost:8080"
