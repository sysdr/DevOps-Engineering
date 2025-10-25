# Day 19: Ingress & Load Balancing Strategies

Advanced traffic management system with SSL automation, rate limiting, and global load balancing.

## Quick Start

```bash
./start.sh    # Start all services
./stop.sh     # Stop all services
```

## Architecture

- **Backend**: FastAPI with Prometheus metrics and Redis rate limiting
- **Frontend**: Modern dashboard with real-time monitoring
- **Ingress**: NGINX with SSL automation and advanced features
- **Monitoring**: Prometheus metrics collection

## Features

- ✅ Automated SSL/TLS with cert-manager
- ✅ Rate limiting with Redis backend
- ✅ Health checks and monitoring
- ✅ Load balancing with multiple backends
- ✅ Real-time metrics dashboard
- ✅ Load testing with Locust

## Testing

```bash
# Unit tests
python -m pytest tests/ -v

# Load testing
locust -f tests/locustfile.py --host=http://localhost:8000
```

## Kubernetes Deployment

```bash
# Install prerequisites
./scripts/install-ingress.sh

# Deploy application
./scripts/deploy.sh
```

## Monitoring

- Backend metrics: http://localhost:8000/metrics
- Dashboard: http://localhost:3000
- Health check: http://localhost:8000/health
