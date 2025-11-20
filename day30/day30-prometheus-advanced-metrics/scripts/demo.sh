#!/bin/bash

# Day 30: Demo Script - Prometheus Advanced Metrics

echo "=============================================="
echo "Prometheus Advanced Metrics Demo"
echo "=============================================="

BASE_URL="http://localhost:8000"
PROMETHEUS_URL="http://localhost:9090"
THANOS_URL="http://localhost:10904"

echo ""
echo "1. Checking Application Health..."
curl -s "$BASE_URL/health" | python3 -m json.tool

echo ""
echo "2. Generating Order Traffic..."
curl -s "$BASE_URL/orders/simulate?count=20" | python3 -m json.tool

echo ""
echo "3. Sample Metrics from Application..."
echo "---"
curl -s "$BASE_URL/metrics" | grep -E "^(http_requests_total|orders_created_total|active_users_total)" | head -20

echo ""
echo "4. Checking Prometheus Targets..."
curl -s "$PROMETHEUS_URL/api/v1/targets" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for target in data.get('data', {}).get('activeTargets', [])[:5]:
    print(f\"  {target.get('labels', {}).get('job', 'unknown')}: {target.get('health', 'unknown')}\")"

echo ""
echo "5. Testing PromQL Query..."
curl -s -g "$PROMETHEUS_URL/api/v1/query?query=sum(rate(http_requests_total[1m]))" | python3 -c "
import sys, json
data = json.load(sys.stdin)
result = data.get('data', {}).get('result', [])
if result:
    print(f\"  Request rate: {float(result[0].get('value', [0, 0])[1]):.2f} req/s\")
else:
    print('  No data yet - try again in a minute')"

echo ""
echo "6. Checking Thanos Query..."
curl -s "$THANOS_URL/api/v1/stores" | python3 -c "
import sys, json
data = json.load(sys.stdin)
stores = data.get('data', [])
print(f\"  Connected stores: {len(stores)}\")"

echo ""
echo "7. Triggering Test Errors..."
for i in {1..5}; do
    curl -s "$BASE_URL/error" > /dev/null
done
echo "  Sent 5 error requests"

echo ""
echo "8. Checking Received Alerts..."
curl -s "$BASE_URL/alerts" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  Total alerts received: {data.get('total', 0)}\")"

echo ""
echo "9. Dashboard Data Summary..."
curl -s "$BASE_URL/dashboard/data" | python3 -c "
import sys, json
data = json.load(sys.stdin)
metrics = data.get('metrics', {})
print(f\"  Active users: {metrics.get('active_users', 0)}\")
print(f\"  Order queue: {metrics.get('queues', {}).get('orders', 0)}\")
print(f\"  DB connections: {metrics.get('database', {}).get('active', 0)} active\")"

echo ""
echo "=============================================="
echo "Demo Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Open Dashboard: http://localhost:3000"
echo "  2. Explore Prometheus: http://localhost:9090"
echo "  3. Check Thanos Query: http://localhost:10904"
echo "  4. Monitor alerts: http://localhost:9093"
