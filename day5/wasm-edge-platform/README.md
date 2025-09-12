# WASM Edge Computing Platform

Ultra-low latency edge computing platform with WebAssembly runtime integration.

## Features

- 🚀 Sub-10ms response times with WASM runtime
- 🌐 Edge-to-cloud data synchronization
- 📊 Real-time performance monitoring
- ☸️  Kubernetes-native deployment
- 📈 Performance benchmarking dashboard

## Quick Start

### Local Development

```bash
# Start the platform
./start.sh

# Stop the platform  
./stop.sh
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Stop
docker-compose down
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
./scripts/deploy/deploy-k8s.sh
```

## Architecture

The platform consists of:

1. **FastAPI Backend** - REST API with WASM runtime integration
2. **React Frontend** - Real-time dashboard for monitoring and control
3. **WASM Modules** - High-performance edge computation units
4. **Kubernetes Orchestration** - Scalable container management
5. **Monitoring Stack** - Prometheus metrics and Grafana dashboards

## API Endpoints

- `POST /compute` - Execute computation on edge
- `POST /sync` - Sync edge data to cloud
- `GET /edge/status` - Platform status
- `GET /performance/benchmark` - Performance comparison
- `GET /metrics` - Prometheus metrics

## Performance

- WASM cold start: <1ms
- Computation latency: <10ms
- Container cold start: 100-500ms
- 3-5x performance improvement over traditional deployments

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run performance tests
python -m pytest tests/test_edge_computing.py::TestPerformance -v
```
