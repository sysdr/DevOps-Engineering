#!/bin/bash

set -e

echo "============================================"
echo "Starting OpenTelemetry Observability Stack"
echo "============================================"

cd "$(dirname "$0")"

# Build and start with Docker Compose
echo "Building and starting services..."
docker-compose up -d --build

echo ""
echo "Waiting for services to be healthy..."

# Wait for collector
echo -n "Waiting for OpenTelemetry Collector..."
until curl -s http://localhost:13133 > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " Ready!"

# Wait for Jaeger
echo -n "Waiting for Jaeger..."
until curl -s http://localhost:16686 > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " Ready!"

# Wait for Prometheus
echo -n "Waiting for Prometheus..."
until curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " Ready!"

# Wait for services
for port in 8000 8001 8002; do
    echo -n "Waiting for service on port $port..."
    until curl -s "http://localhost:$port/health" > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " Ready!"
done

# Wait for dashboard
echo -n "Waiting for Dashboard..."
sleep 10
echo " Ready!"

echo ""
echo "============================================"
echo "All Services Running!"
echo "============================================"
echo ""
echo "Services:"
echo "  • Order Service:     http://localhost:8000"
echo "  • Inventory Service: http://localhost:8001"
echo "  • Payment Service:   http://localhost:8002"
echo ""
echo "Observability:"
echo "  • Dashboard:         http://localhost:3000"
echo "  • Jaeger UI:         http://localhost:16686"
echo "  • Prometheus:        http://localhost:9090"
echo "  • Collector zPages:  http://localhost:55679/debug/tracez"
echo "  • Metrics Endpoint:  http://localhost:8889/metrics"
echo ""
echo "Run demo: ./scripts/demo.sh"
echo "Stop all: ./stop.sh"
