#!/bin/bash

set -e

echo "=================================================="
echo "Running MLOps Security & Governance Demo"
echo "=================================================="
echo ""

# Test security validation
echo "1. Testing Security Gateway..."
echo "   Testing normal input..."
curl -s -X POST http://localhost:8000/api/security/validate \
  -H "Content-Type: application/json" \
  -d '{"model_id":"fraud_detection_v1","input":{"features":[0.5,0.3,0.8]}}' | python3 -m json.tool

echo ""
echo "   Testing adversarial input..."
curl -s -X POST http://localhost:8000/api/security/validate \
  -H "Content-Type: application/json" \
  -d '{"model_id":"fraud_detection_v1","input":{"features":[5.0,5.0,5.0]}}' | python3 -m json.tool

# Test governance workflow
echo ""
echo "2. Testing Governance Workflow..."
echo "   Submitting model for approval..."
WORKFLOW=$(curl -s -X POST http://localhost:8000/api/governance/submit \
  -H "Content-Type: application/json" \
  -d '{"model_id":"fraud_detection_v2","metadata":{"version":"2.0.0","algorithm":"XGBoost"}}')
echo $WORKFLOW | python3 -m json.tool

WORKFLOW_ID=$(echo $WORKFLOW | python3 -c "import sys, json; print(json.load(sys.stdin)['workflow_id'])")
echo ""
echo "   Approving data validation stage..."
curl -s -X POST http://localhost:8000/api/governance/approve \
  -H "Content-Type: application/json" \
  -d "{\"workflow_id\":\"$WORKFLOW_ID\",\"stage\":\"data_validated\",\"approver\":\"data-team-lead\",\"decision\":\"approved\"}" | python3 -m json.tool

# Test bias analysis
echo ""
echo "3. Testing Bias Monitor..."
curl -s -X POST http://localhost:8000/api/bias/analyze \
  -H "Content-Type: application/json" \
  -d '{"model_id":"fraud_detection_v1","predictions":[{"predicted":true,"actual":true,"demographic":"group_a"},{"predicted":false,"actual":false,"demographic":"group_a"},{"predicted":true,"actual":true,"demographic":"group_b"},{"predicted":true,"actual":false,"demographic":"group_b"}]}' | python3 -m json.tool

# Get model card
echo ""
echo "4. Generating Model Card..."
curl -s http://localhost:8000/api/compliance/model-card/fraud_detection_v1 | python3 -m json.tool

# Verify audit chain
echo ""
echo "5. Verifying Audit Chain Integrity..."
curl -s http://localhost:8000/api/audit/verify | python3 -m json.tool

echo ""
echo "=================================================="
echo "✅ Demo Complete!"
echo "=================================================="
echo ""
echo "📊 Open http://localhost:3000 to view the dashboard"
