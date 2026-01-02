#!/bin/bash

echo "Stopping AI Infrastructure Management Platform..."

if [ -f .pids ]; then
    while read pid; do
        kill $pid 2>/dev/null
    done < .pids
    rm .pids
fi

docker stop timescaledb-ai 2>/dev/null
docker rm timescaledb-ai 2>/dev/null

echo "✅ All services stopped"
