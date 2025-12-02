#!/bin/bash

echo "=== Distributed Tracing Demo ==="
echo ""

echo "1. Checking service health..."
curl -s http://localhost:8001/health | python3 -m json.tool
curl -s http://localhost:8002/health | python3 -m json.tool
curl -s http://localhost:8003/health | python3 -m json.tool

echo ""
echo "2. Creating orders to generate traces..."

for i in {1..5}; do
  echo "Order $i:"
  curl -s -X POST http://localhost:8001/orders \
    -H "Content-Type: application/json" \
    -d '{
      "customer_id": "CUST-DEMO-'$i'",
      "items": [
        {"product_id": "PROD-001", "quantity": 2, "price": 49.99},
        {"product_id": "PROD-004", "quantity": 1, "price": 199.99}
      ]
    }' | python3 -m json.tool
  sleep 2
done

echo ""
echo "3. View traces at: http://localhost:16686"
echo "4. View APM Dashboard at: http://localhost:3000"
echo ""
echo "Traces show complete request flow through all services!"
