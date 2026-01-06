#!/bin/bash

echo "==================================================="
echo "AI Ethics & Governance Platform - Live Demo"
echo "==================================================="

# Wait for services
sleep 2

echo ""
echo "1. Testing Bias Detection Service..."
echo "---------------------------------------------------"
curl -X POST http://localhost:8001/api/v1/bias/analyze \
  -H "Content-Type: application/json" \
  -d '{"model_id": "demo-model-1", "dataset_id": "demo-data-1"}' \
  2>/dev/null | python -m json.tool

echo ""
echo "2. Logging Fairness Metrics..."
echo "---------------------------------------------------"
for i in {1..5}; do
  curl -X POST http://localhost:8002/api/v1/monitor/log \
    -H "Content-Type: application/json" \
    -d "{\"model_id\": \"demo-model-1\", \"prediction\": 0.$((RANDOM % 10)), \"group\": \"Group_A\"}" \
    2>/dev/null
done
echo "Logged 5 predictions"

echo ""
echo "3. Getting Current Fairness Metrics..."
echo "---------------------------------------------------"
curl http://localhost:8002/api/v1/monitor/metrics/demo-model-1 2>/dev/null | python -m json.tool

echo ""
echo "4. Generating AI Explanation..."
echo "---------------------------------------------------"
curl -X POST http://localhost:8003/api/v1/explain/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "demo-model-1",
    "prediction_id": "demo-pred-1",
    "input_data": {"credit_score": 720, "income": 75000, "debt_ratio": 0.25, "age": 35},
    "prediction": 0.85
  }' 2>/dev/null | python -m json.tool

echo ""
echo "5. Submitting Model to Governance Workflow..."
echo "---------------------------------------------------"
curl -X POST http://localhost:8004/api/v1/governance/submit \
  -H "Content-Type: application/json" \
  -d '{"model_id": "demo-model-2", "owner": "demo@example.com"}' \
  2>/dev/null | python -m json.tool

echo ""
echo "==================================================="
echo "Demo Complete! Visit http://localhost:3000 to see"
echo "the full dashboard with visualizations"
echo "==================================================="
