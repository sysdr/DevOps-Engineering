#!/bin/bash

echo "=== Stopping Day 33 Distributed Tracing System ==="

# Kill services
if [ -f .pids ]; then
  while read pid; do
    kill $pid 2>/dev/null
  done < .pids
  rm .pids
fi

# Stop Jaeger
docker stop jaeger 2>/dev/null
docker rm jaeger 2>/dev/null

# Deactivate virtual environment
deactivate 2>/dev/null

echo "All services stopped"
