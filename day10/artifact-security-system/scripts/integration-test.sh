#!/bin/bash
echo "🧪 Running Integration Tests..."

# Test backend health
echo "Testing backend health..."
curl -f http://localhost:8000/api/health || exit 1

# Test image signing
echo "Testing image signing..."
curl -X POST http://localhost:8000/api/sign \
  -H "Content-Type: application/json" \
  -d '{"image": "nginx", "tag": "latest"}' || exit 1

# Test vulnerability scanning
echo "Testing vulnerability scanning..."
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"image": "nginx:latest"}' || exit 1

# Test policy evaluation
echo "Testing policy evaluation..."
curl -X POST http://localhost:8000/api/policy/evaluate \
  -H "Content-Type: application/json" \
  -d '{"image": "nginx:latest"}' || exit 1

echo "✅ All integration tests passed!"
