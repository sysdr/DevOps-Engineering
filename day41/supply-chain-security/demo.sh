#!/bin/bash

echo "Running automated demo..."
sleep 2

# Create artifact
curl -s -X POST http://localhost:8000/api/artifacts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "demo-app-1",
    "name": "demo-application",
    "version": "1.0.0",
    "type": "container",
    "registry": "docker.io",
    "created_at": "2024-12-10T00:00:00Z"
  }' | python3 -m json.tool

echo ""
echo "✓ Artifact created"
sleep 1

# Generate SBOM
curl -s -X POST http://localhost:8000/api/sbom/generate \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "demo-app-1",
    "image_name": "demo-application:latest"
  }' | python3 -m json.tool

echo ""
echo "✓ SBOM generated"
sleep 1

# Sign artifact
curl -s -X POST http://localhost:8000/api/sign \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "demo-app-1",
    "signer": "demo-ci@company.com"
  }' | python3 -m json.tool

echo ""
echo "✓ Artifact signed"
sleep 1

# Verify signature
curl -s -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "demo-app-1"
  }' | python3 -m json.tool

echo ""
echo "✓ Signature verified"
sleep 1

# Scan vulnerabilities
curl -s -X POST http://localhost:8000/api/scan/vulnerabilities \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "demo-app-1"
  }' | python3 -m json.tool

echo ""
echo "✓ Vulnerability scan complete"
echo ""
echo "Check the dashboard at http://localhost:3000"
