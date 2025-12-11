#!/bin/bash

echo "=========================================="
echo "Container Security Platform Demo"
echo "=========================================="

API_BASE="http://localhost"

echo ""
echo "1. Scanning vulnerable image..."
curl -X POST "${API_BASE}:8001/scan" \
  -H "Content-Type: application/json" \
  -d '{"image": "vulnerable-image:old", "policy": "default"}' \
  2>/dev/null | python3 -m json.tool

sleep 3

echo ""
echo "2. Getting scan results..."
curl "${API_BASE}:8001/scans" 2>/dev/null | python3 -m json.tool

echo ""
echo "3. Checking runtime alerts..."
curl "${API_BASE}:8002/alerts?limit=5" 2>/dev/null | python3 -m json.tool

echo ""
echo "4. Viewing admission decisions..."
curl "${API_BASE}:8003/decisions?limit=5" 2>/dev/null | python3 -m json.tool

echo ""
echo "5. Running CIS benchmark..."
curl -X POST "${API_BASE}:8004/benchmark/run" 2>/dev/null | python3 -m json.tool

sleep 3

echo ""
echo "6. Getting benchmark results..."
curl "${API_BASE}:8004/benchmark/latest" 2>/dev/null | python3 -m json.tool

echo ""
echo "=========================================="
echo "Demo Complete!"
echo "Visit http://localhost:3000 for the dashboard"
echo "=========================================="
