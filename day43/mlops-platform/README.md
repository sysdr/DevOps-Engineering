# Day 43: MLOps Platform

Production-grade MLOps platform with experiment tracking, model serving, and monitoring.

## Architecture

- **MLflow Server**: Experiment tracking and model registry
- **Training Service**: Automated model training with job orchestration
- **Model Serving**: Production inference endpoints with versioning
- **Monitoring Service**: Drift detection and performance monitoring
- **ML Dashboard**: Real-time visualization and control

## Quick Start

### With Docker (Recommended)

```bash
# Start all services
./start.sh

# Start the dashboard (in a new terminal)
cd ml-dashboard && npm start

# Run demo
./demo.sh

# Stop all services
./stop.sh
```

### Without Docker

```bash
# Terminal 1: Start backend services
python3.11 -m venv venv
source venv/bin/activate
pip install -r training-service/requirements.txt
uvicorn training-service.app.main:app --port 8000

# Terminal 2: Start serving
uvicorn model-serving.app.main:app --port 8001

# Terminal 3: Start monitoring
uvicorn monitoring-service.app.main:app --port 8002

# Terminal 4: Start dashboard
cd ml-dashboard && npm install && npm start
```

## Usage

### Submit Training Job

```bash
curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_name": "fraud_detection",
    "model_type": "random_forest",
    "hyperparameters": {
      "n_estimators": 100,
      "max_depth": 10
    },
    "dataset_config": {
      "n_samples": 1000,
      "n_features": 20
    }
  }'
```

### Make Predictions

```bash
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "fraud_detection_random_forest",
    "version": "Production",
    "features": [[0.5, -0.3, ..., 0.1]]
  }'
```

### Check Drift

```bash
curl http://localhost:8002/drift/fraud_detection_random_forest
```

## Web Interfaces

- MLflow UI: http://localhost:5000
- ML Dashboard: http://localhost:3000
- MinIO Console: http://localhost:9001 (admin/minioadmin)
- Training API Docs: http://localhost:8000/docs
- Serving API Docs: http://localhost:8001/docs
- Monitoring API Docs: http://localhost:8002/docs

## Testing

```bash
pytest tests/ -v
```

## Project Structure

```
mlops-platform/
├── mlflow-server/        # MLflow tracking server
├── training-service/     # Model training orchestration
├── model-serving/        # Production inference API
├── monitoring-service/   # Drift and performance monitoring
├── ml-dashboard/         # React dashboard
├── tests/                # Integration tests
├── docker-compose.yml    # Multi-service orchestration
└── scripts/              # Utility scripts
```

## Key Features

- ✅ Complete ML lifecycle management
- ✅ Experiment tracking with MLflow
- ✅ Model versioning and staging
- ✅ Production serving with A/B testing capability
- ✅ Real-time drift detection
- ✅ Performance monitoring
- ✅ Modern React dashboard
- ✅ Docker-based deployment
- ✅ Comprehensive testing

## Next Steps

- Add distributed training with Ray
- Implement feature store
- Add model explainability (SHAP)
- Integrate CI/CD pipelines
- Add authentication/authorization
- Implement automated retraining
