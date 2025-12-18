#!/bin/bash

echo "=== Security Assessment Platform Demo ==="
echo ""

API_URL="http://localhost:8000"

# Wait for API to be ready
echo "Checking API status..."
for i in {1..10}; do
    if curl -s ${API_URL}/health > /dev/null 2>&1; then
        echo "✅ API is ready"
        break
    fi
    sleep 1
done

# Run security assessment
echo ""
echo "1. Running full security assessment..."
ASSESSMENT_RESPONSE=$(curl -s -X POST ${API_URL}/api/assessment/run)
ASSESSMENT_ID=$(echo $ASSESSMENT_RESPONSE | grep -o '"assessment_id":"[^"]*"' | cut -d'"' -f4)
echo "   Assessment ID: $ASSESSMENT_ID"

# Wait for assessment to complete
echo "   Waiting for assessment to complete..."
for i in {1..30}; do
    RESULT=$(curl -s ${API_URL}/api/assessment/results/$ASSESSMENT_ID)
    STATUS=$(echo $RESULT | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$STATUS" = "completed" ]; then
        echo "   ✅ Assessment completed!"
        break
    fi
    sleep 2
done

# Get latest results
echo ""
echo "2. Fetching assessment results..."
curl -s ${API_URL}/api/assessment/results/latest | python3 -m json.tool | head -50

# Run penetration tests
echo ""
echo "3. Running penetration tests..."
curl -s -X POST "${API_URL}/api/pentest/run?test_suite=full" | python3 -m json.tool

# Get compliance report
echo ""
echo "4. Generating SOC 2 compliance report..."
curl -s ${API_URL}/api/compliance/report/soc2 | python3 -m json.tool

# Get playbooks
echo ""
echo "5. Listing available incident response playbooks..."
curl -s ${API_URL}/api/playbooks | python3 -m json.tool

# Get score history
echo ""
echo "6. Fetching security score history..."
curl -s ${API_URL}/api/metrics/score-history | python3 -m json.tool

echo ""
echo "=== Demo Complete ==="
echo "Open http://localhost:3000 to view the dashboard"
