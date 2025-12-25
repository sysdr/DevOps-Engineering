# Model Serving Platform

Production-grade ML model serving with A/B testing, auto-scaling, and inference optimization.

## Features

- ✅ Multiple model version deployment
- ✅ A/B testing with traffic splitting
- ✅ Auto-scaling based on load
- ✅ Model quantization for efficiency
- ✅ Real-time monitoring dashboard
- ✅ Prometheus metrics integration
- ✅ Kubernetes-ready manifests

## Quick Start

### Local Development

```bash
# Start all services
./start.sh

# Run demo
python scripts/demo.py

# Load test
python scripts/load_test.py

# Stop services
./stop.sh
```

### Docker Deployment

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Kubernetes Deployment

```bash
# Deploy v1
kubectl apply -f k8s/inference-service-v1.yaml

# Deploy v2 (canary)
kubectl apply -f k8s/inference-service-v2.yaml

# Enable auto-scaling
kubectl apply -f k8s/hpa.yaml
```

## Testing

```bash
# Run tests
source venv/bin/activate
pytest tests/ -v

# With coverage
pytest tests/ --cov=backend --cov-report=html
```

## API Endpoints

- `POST /v1/models/predict` - Make prediction
- `GET /v1/models` - List models
- `GET /v1/traffic-split` - Get traffic configuration
- `POST /v1/traffic-split` - Update traffic split
- `GET /v1/metrics/{version}` - Get model metrics
- `GET /metrics` - Prometheus metrics

## Accessing Services

- Dashboard: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

## Model Serving Patterns

### Canary Deployment
```bash
# Start with 10% traffic to v2
curl -X POST http://localhost:8000/v1/traffic-split \
  -H "Content-Type: application/json" \
  -d '{"v1": 90, "v2": 10}'

# Gradually increase
curl -X POST http://localhost:8000/v1/traffic-split \
  -H "Content-Type: application/json" \
  -d '{"v1": 50, "v2": 50}'
```

### Model Quantization
```python
# Models are pre-quantized (4x smaller, 2-4x faster)
response = requests.post(
    "http://localhost:8000/v1/models/predict",
    json={
        "instances": [[5.1, 3.5, 1.4, 0.2]],
        "version": "v2-quantized"
    }
)
```

## Monitoring

Metrics tracked per model version:
- Request rate
- Latency (p50, p95, p99)
- Error rate
- Prediction distribution
- Resource utilization

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Ingress   │ (Traffic Split)
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌─────┐
│ v1  │ │ v2  │ (Model Servers)
└──┬──┘ └──┬──┘
   │       │
   └───┬───┘
       ▼
  ┌─────────┐
  │  Redis  │ (Cache)
  └─────────┘
```

## Real-World Usage

This platform demonstrates patterns used by:
- Netflix for recommendation models
- Uber for ETA predictions
- Spotify for playlist recommendations

## Next Steps

1. Add drift detection (Day 47)
2. Implement model explainability
3. Add fairness monitoring
4. Integrate with existing observability stack
