#!/bin/bash

echo "Stopping Container Security Platform..."

if [ -f scanner.pid ]; then
    kill $(cat scanner.pid) 2>/dev/null
    rm scanner.pid
fi

if [ -f monitor.pid ]; then
    kill $(cat monitor.pid) 2>/dev/null
    rm monitor.pid
fi

if [ -f admission.pid ]; then
    kill $(cat admission.pid) 2>/dev/null
    rm admission.pid
fi

if [ -f benchmark.pid ]; then
    kill $(cat benchmark.pid) 2>/dev/null
    rm benchmark.pid
fi

if [ -f dashboard.pid ]; then
    kill $(cat dashboard.pid) 2>/dev/null
    rm dashboard.pid
fi

echo "All services stopped"
