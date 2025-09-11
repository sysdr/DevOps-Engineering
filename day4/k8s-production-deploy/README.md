# Kubernetes Production Dashboard

A production-grade Kubernetes monitoring dashboard with autoscaling, network policies, and security features.

## Features

- 🎯 Real-time cluster monitoring
- 📊 Interactive dashboard with React frontend
- 🔄 Horizontal Pod Autoscaling (HPA) 
- 🛡️ Zero-trust network policies
- 📈 Prometheus metrics integration
- 🔒 Security best practices
- 🐳 Containerized deployment

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker
- kubectl (for Kubernetes deployment)

### Local Development

1. **Start the application:**
   ```bash
   bash start.sh
   ```

2. **Access the dashboard:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Metrics: http://localhost:5000/metrics

3. **Stop the application:**
   ```bash
   bash stop.sh
   ```

### Production Deployment

1. **Build Docker images:**
   ```bash
   bash scripts/build.sh
   ```

2. **Run tests:**
   ```bash
   bash scripts/test.sh
   ```

3. **Deploy to Kubernetes:**
   ```bash
   bash scripts/deploy.sh
   ```

## Architecture

The application follows a microservices architecture:

- **Frontend**: React SPA with modern dashboard UI
- **Backend**: Flask API with Kubernetes integration
- **Monitoring**: Prometheus metrics and health checks
- **Security**: Network policies and RBAC

## API Endpoints

- `GET /health` - Health check
- `GET /api/cluster/info` - Cluster information
- `GET /api/autoscaling/status` - HPA status
- `GET /api/network/policies` - Network policies
- `GET /metrics` - Prometheus metrics

## Development

### Project Structure

```
k8s-production-deploy/
├── src/
│   ├── backend/           # Flask API
│   └── frontend/          # React dashboard
├── k8s/                   # Kubernetes manifests
├── terraform/             # Infrastructure as code
├── tests/                 # Test files
├── scripts/               # Build and deployment scripts
└── monitoring/            # Monitoring configuration
```

### Running Tests

```bash
# Unit tests
python -m pytest tests/test_backend.py -v

# Integration tests
python -m pytest tests/test_integration.py -v

# Security scan
bandit -r src/backend/
```

## Production Considerations

- Use managed EKS for production clusters
- Implement proper secret management
- Configure resource quotas and limits
- Set up monitoring and alerting
- Regular security updates

## License

MIT License
