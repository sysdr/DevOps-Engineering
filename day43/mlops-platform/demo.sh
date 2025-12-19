#!/bin/bash

set -e

echo "=========================================="
echo "MLOps Platform Demo"
echo "=========================================="

# Submit training job
echo ""
echo "1. Submitting training job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_name": "fraud_detection_demo",
    "model_type": "random_forest",
    "hyperparameters": {
      "n_estimators": 100,
      "max_depth": 10,
      "random_state": 42
    },
    "dataset_config": {
      "n_samples": 1000,
      "n_features": 20
    },
    "tags": {
      "demo": "true",
      "env": "production"
    }
  }')

JOB_ID=$(echo $JOB_RESPONSE | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)
echo "Job submitted: $JOB_ID"

# Wait for job completion
echo ""
echo "2. Waiting for training to complete..."
for i in {1..60}; do
    STATUS=$(curl -s http://localhost:8000/jobs/$JOB_ID | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    echo "Status: $STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✓ Training completed successfully!"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "✗ Training failed"
        exit 1
    fi
    
    sleep 5
done

# Get job metrics
echo ""
echo "3. Training Metrics:"
curl -s http://localhost:8000/jobs/$JOB_ID | grep -o '"metrics":{[^}]*}' | sed 's/,/\n/g'

# Register model (Note: In actual MLflow, this happens automatically in training)
echo ""
echo "4. Model registered in MLflow"
echo "View at: http://localhost:5000"

# Make predictions
echo ""
echo "5. Making predictions..."
PRED_RESPONSE=$(curl -s -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "fraud_detection_demo_random_forest",
    "version": "Production",
    "features": [[0.5, -0.3, 0.8, -0.2, 0.1, 0.4, -0.6, 0.2, 0.9, -0.1, 0.3, -0.4, 0.6, 0.1, -0.7, 0.2, 0.5, -0.3, 0.4, 0.1]]
  }')

echo "Prediction result:"
echo $PRED_RESPONSE | grep -o '"predictions":\[[^]]*\]' | sed 's/,/\n/g'

# Check monitoring
echo ""
echo "6. Checking model performance..."
curl -s http://localhost:8002/performance/fraud_detection_demo_random_forest | grep -o '"total_predictions":[0-9]*' | cut -d':' -f2

# Check drift
echo ""
echo "7. Checking for model drift..."
curl -s http://localhost:8002/drift/fraud_detection_demo_random_forest | grep -o '"drift_score":[^,]*' | cut -d':' -f2

echo ""
echo "=========================================="
echo "Demo completed successfully!"
echo "=========================================="
echo ""
echo "Explore the platform:"
echo "- MLflow UI: http://localhost:5000"
echo "- Dashboard: http://localhost:3000"
echo "- API docs: http://localhost:8000/docs"
