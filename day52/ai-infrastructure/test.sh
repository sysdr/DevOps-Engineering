#!/bin/bash

echo "Testing AI Infrastructure Management..."

# Wait for services
sleep 5

echo "1. Testing API health..."
curl -s http://localhost:8000/api/health | jq

echo ""
echo "2. Testing metrics collection..."
curl -s http://localhost:8000/api/metrics/current | jq '. | to_entries | .[0]'

echo ""
echo "3. Training models..."
curl -s -X POST http://localhost:8000/api/models/train | jq

sleep 30

echo ""
echo "4. Testing predictions..."
curl -s http://localhost:8000/api/predictions/cpu_usage_percent | jq

echo ""
echo "5. Checking anomalies..."
curl -s http://localhost:8000/api/anomalies/recent | jq '. | length'

echo ""
echo "6. Checking scaling decisions..."
curl -s http://localhost:8000/api/scaling/decisions | jq '. | length'

echo ""
echo "7. Dashboard stats..."
curl -s http://localhost:8000/api/dashboard/stats | jq

echo ""
echo "============================================"
echo "✅ All tests completed"
echo "Open http://localhost:3000 to view dashboard"
echo "============================================"
