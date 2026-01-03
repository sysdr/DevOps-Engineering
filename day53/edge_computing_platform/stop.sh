#!/bin/bash

echo "Stopping Edge Computing Platform..."

if [ -f /tmp/edge_backend.pid ]; then
    kill $(cat /tmp/edge_backend.pid) 2>/dev/null || true
    rm /tmp/edge_backend.pid
fi

if [ -f /tmp/edge_agent1.pid ]; then
    kill $(cat /tmp/edge_agent1.pid) 2>/dev/null || true
    rm /tmp/edge_agent1.pid
fi

if [ -f /tmp/edge_agent2.pid ]; then
    kill $(cat /tmp/edge_agent2.pid) 2>/dev/null || true
    rm /tmp/edge_agent2.pid
fi

if [ -f /tmp/edge_agent3.pid ]; then
    kill $(cat /tmp/edge_agent3.pid) 2>/dev/null || true
    rm /tmp/edge_agent3.pid
fi

echo "✅ Platform stopped"
