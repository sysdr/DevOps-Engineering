#!/bin/bash

echo "Stopping AI DevOps Platform..."

# Kill services by PID
if [ -f .code_analyzer.pid ]; then
    kill $(cat .code_analyzer.pid) 2>/dev/null
    rm .code_analyzer.pid
fi

if [ -f .log_analyzer.pid ]; then
    kill $(cat .log_analyzer.pid) 2>/dev/null
    rm .log_analyzer.pid
fi

if [ -f .incident_manager.pid ]; then
    kill $(cat .incident_manager.pid) 2>/dev/null
    rm .incident_manager.pid
fi

if [ -f .doc_generator.pid ]; then
    kill $(cat .doc_generator.pid) 2>/dev/null
    rm .doc_generator.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi

# Kill any remaining uvicorn and node processes
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null

echo "✓ All services stopped"
