#!/bin/bash

echo "Stopping OpenTelemetry Observability Stack..."

cd "$(dirname "$0")"

docker-compose down -v

echo "All services stopped."
