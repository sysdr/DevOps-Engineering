# Day 26: Infrastructure GitOps with Crossplane

## Quick Start

### Without Docker
```bash
source venv/bin/activate
./start.sh
```

### With Docker
```bash
docker-compose up --build
```

## Access
- API: http://localhost:8000
- Dashboard: http://localhost:8080 (Docker) or open frontend/index.html
- API Docs: http://localhost:8000/docs

## Testing
```bash
pytest tests/ -v
```

## Prerequisites for Full Functionality
- Kubernetes cluster with Crossplane installed
- AWS/GCP provider configured
- kubectl configured

## Stopping
```bash
./stop.sh  # Without Docker
docker-compose down  # With Docker
```
