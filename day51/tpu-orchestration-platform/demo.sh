#!/bin/bash

echo "=========================================="
echo "TPU Orchestration Platform Demo"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"

echo "1. Checking platform status..."
curl -s $BASE_URL/ | python3 -m json.tool
echo ""

echo "2. Submitting high-priority training job..."
JOB1=$(curl -s -X POST $BASE_URL/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-large-critical",
    "tpu_type": "v4-8",
    "priority": 90,
    "optimize_cost": true,
    "total_steps": 1000
  }' | python3 -m json.tool)
echo "$JOB1"
JOB1_ID=$(echo "$JOB1" | grep -o '"job_id": "[^"]*' | cut -d'"' -f4)
echo ""

echo "3. Submitting cost-optimized batch job..."
JOB2=$(curl -s -X POST $BASE_URL/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "bert-base-batch",
    "tpu_type": "v4-32",
    "priority": 30,
    "optimize_cost": true,
    "use_preemptible": true,
    "total_steps": 5000
  }' | python3 -m json.tool)
echo "$JOB2"
JOB2_ID=$(echo "$JOB2" | grep -o '"job_id": "[^"]*' | cut -d'"' -f4)
echo ""

echo "4. Submitting medium-priority job..."
JOB3=$(curl -s -X POST $BASE_URL/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "roberta-large",
    "tpu_type": "v4-8",
    "priority": 60,
    "optimize_cost": true,
    "total_steps": 2000
  }' | python3 -m json.tool)
echo "$JOB3"
echo ""

echo "5. Waiting for jobs to start..."
sleep 8
echo ""

echo "6. Checking job status..."
if [ ! -z "$JOB1_ID" ]; then
    echo "High-priority job:"
    curl -s $BASE_URL/api/jobs/$JOB1_ID | python3 -m json.tool
    echo ""
fi
echo ""

echo "7. Listing all jobs..."
curl -s $BASE_URL/api/jobs | python3 -m json.tool
echo ""

echo "8. Checking cluster metrics..."
curl -s $BASE_URL/api/metrics/cluster | python3 -m json.tool
echo ""

echo "=========================================="
echo "Demo completed successfully!"
echo "=========================================="
echo ""
echo "Open http://localhost:3000 to view the dashboard"
echo "Monitor real-time metrics and job progress"
echo ""
