#!/bin/bash

set -e

echo "=========================================="
echo "Starting MLOps Platform"
echo "=========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check for docker compose (plugin) or docker-compose (legacy)
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Build and start services
echo "Building Docker images..."
$DOCKER_COMPOSE build

echo "Starting services..."
$DOCKER_COMPOSE up -d

echo "Waiting for services to be healthy..."
sleep 30

# Check service health
echo "Checking service health..."
# MLflow doesn't have /health endpoint, check root instead
services=("http://localhost:5000/" "http://localhost:8000/health" "http://localhost:8001/health" "http://localhost:8002/health")
service_names=("MLflow" "Training Service" "Serving Service" "Monitoring Service")
for i in "${!services[@]}"; do
    service="${services[$i]}"
    name="${service_names[$i]}"
    echo "Checking $name..."
    max_retries=30
    retry=0
    while [ $retry -lt $max_retries ]; do
        if curl -f -s "$service" > /dev/null 2>&1; then
            echo "✓ $name is healthy"
            break
        fi
        retry=$((retry + 1))
        sleep 2
    done
    if [ $retry -eq $max_retries ]; then
        echo "✗ $name failed to start (checking $service)"
    fi
done

# Create MinIO bucket (wait a bit for MinIO to be ready)
echo "Setting up MinIO bucket..."
sleep 10
$DOCKER_COMPOSE exec -T minio mc alias set myminio http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
$DOCKER_COMPOSE exec -T minio mc mb myminio/mlflow-artifacts 2>/dev/null || true

# Install dashboard dependencies and start
echo "Setting up ML Dashboard..."
cd ml-dashboard
if [ ! -d "node_modules" ]; then
    npm install
fi

echo ""
echo "=========================================="
echo "MLOps Platform is running!"
echo "=========================================="
echo "MLflow UI:         http://localhost:5000"
echo "Training API:      http://localhost:8000"
echo "Serving API:       http://localhost:8001"
echo "Monitoring API:    http://localhost:8002"
echo "MinIO Console:     http://localhost:9001"
echo ""
echo "Starting Dashboard..."
echo "Dashboard:         http://localhost:3000"
echo ""
echo "Run 'npm start' in ml-dashboard/ to start the UI"
echo "Run './demo.sh' to see the platform in action"
echo "Run './stop.sh' to stop all services"
