#!/bin/bash

API_URL="http://localhost:8000"

echo "=== Secrets Management System Demo ==="
echo ""

echo "1. Storing secrets in Vault..."
curl -s -X POST "$API_URL/vault/secrets" \
  -H "Content-Type: application/json" \
  -d '{"path":"database/prod/password","data":{"password":"SuperSecret123!"}}' | jq .
sleep 1

echo -e "\n2. Retrieving secret..."
curl -s "$API_URL/vault/secrets/database/prod/password" | jq .
sleep 1

echo -e "\n3. Issuing certificate..."
curl -s -X POST "$API_URL/certificates/issue" \
  -H "Content-Type: application/json" \
  -d '{"domain":"app.example.com","issuer":"letsencrypt"}' | jq .
sleep 1

echo -e "\n4. Generating dynamic database credentials..."
curl -s -X POST "$API_URL/dynamic/database" \
  -H "Content-Type: application/json" \
  -d '{"role":"readonly","ttl_hours":24}' | jq .
sleep 1

echo -e "\n5. Adding rotation policy..."
curl -s -X POST "$API_URL/rotation/policies" \
  -H "Content-Type: application/json" \
  -d '{"path":"database/prod/password","interval_hours":168}' | jq .
sleep 1

echo -e "\n6. Syncing to Kubernetes..."
curl -s -X POST "$API_URL/external-secrets/sync" \
  -H "Content-Type: application/json" \
  -d '{"vault_path":"database/prod/password","k8s_namespace":"production","k8s_secret_name":"db-password"}' | jq .
sleep 1

echo -e "\n7. Checking system statistics..."
curl -s "$API_URL/stats" | jq .
sleep 1

echo -e "\n8. Viewing audit logs..."
curl -s "$API_URL/vault/audit?limit=5" | jq .

echo -e "\n=== Demo Complete ==="
echo "Visit http://localhost:3000 for the full dashboard"
