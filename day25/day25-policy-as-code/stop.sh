#!/bin/bash

echo "Stopping Policy as Code Dashboard..."

if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null
    rm backend.pid
    echo "✓ Backend stopped"
fi

if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
    echo "✓ Frontend stopped"
fi

echo "All services stopped"
