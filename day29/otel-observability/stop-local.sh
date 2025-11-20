#!/bin/bash

cd "$(dirname "$0")"

if [ -f .local-pids ]; then
    echo "Stopping local services..."
    kill $(cat .local-pids) 2>/dev/null || true
    rm .local-pids
fi

echo "Stopping infrastructure..."
docker-compose down otel-collector jaeger prometheus

echo "Local environment stopped."
