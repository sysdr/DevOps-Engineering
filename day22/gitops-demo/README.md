# Day 22: GitOps Fundamentals with Argo CD

This project demonstrates GitOps principles using a simulated Argo CD environment with a Python FastAPI backend and React frontend.

## Quick Start

```bash
./start.sh    # Start the demo
./stop.sh     # Stop the demo
```

## Architecture

- **Backend**: FastAPI application simulating GitOps operations
- **Frontend**: React dashboard showing application sync status
- **GitOps**: Declarative Kubernetes manifests for multi-environment deployment

## Features

- ✅ Application sync status monitoring
- ✅ Manual sync triggers
- ✅ Multi-environment workflows (dev/staging/prod)
- ✅ Health monitoring and metrics
- ✅ Modern UI with Material-UI components

## URLs

- Frontend Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Testing

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Frontend tests  
cd frontend && npm test

# Integration tests
python -m pytest tests/ -v
```
