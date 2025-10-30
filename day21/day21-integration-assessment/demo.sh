#!/bin/bash

echo "🎬 Day 21: Integration Assessment Demo"
echo "===================================="

echo "🔍 Testing all API endpoints..."

echo ""
echo "1. Health Check:"
curl -s http://localhost:8000/api/health | jq '.'

echo ""
echo "2. Running Integration Tests:"
curl -s -X POST http://localhost:8000/api/integration-tests/run | jq '.summary'

echo ""
echo "3. Performance Report:"
curl -s http://localhost:8000/api/performance/report | jq '.report.optimization_score'

echo ""
echo "4. Cost Analysis:"
curl -s http://localhost:8000/api/cost-analysis/report | jq '.analysis.optimization_score'

echo ""
echo "5. Generating Architecture Documentation:"
curl -s -X POST "http://localhost:8000/api/documentation/generate?doc_type=architecture" | jq '.status'

echo ""
echo "✅ Demo completed! Check the dashboard at http://localhost:3000"
