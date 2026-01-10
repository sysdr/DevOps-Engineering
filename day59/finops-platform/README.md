# FinOps Platform - Day 59

Production-grade cost optimization and FinOps implementation for Kubernetes.

## Features

- Real-time cost tracking and attribution
- Intelligent anomaly detection
- Automated optimization recommendations
- Commitment and reserved instance optimization
- Multi-tenant cost allocation
- Interactive dashboard with live updates

## Quick Start

### Local Development

```bash
# Start all services
./start.sh

# Access the platform
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# Stop services
./stop.sh
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Stop services
docker-compose down
```

## API Endpoints

- `GET /api/v1/cost/total` - Get total cluster cost
- `GET /api/v1/cost/namespaces` - Get cost by namespace
- `GET /api/v1/cost/trend` - Get cost trend data
- `GET /api/v1/optimize/recommendations` - Get optimization recommendations
- `GET /api/v1/alerts/` - Get active cost anomaly alerts
- `WS /ws/cost-stream` - WebSocket for real-time updates

## Testing

```bash
source venv/bin/activate
cd backend
pytest tests/ -v
```

## Architecture

The platform consists of:
- FastAPI backend for cost collection and analysis
- React frontend for visualization
- Real-time WebSocket updates
- TimescaleDB for time-series cost data
- Prometheus metrics export

## Cost Optimization Features

1. **Rightsizing** - Identify overprovisioned resources
2. **Commitment Optimization** - Reserved instance recommendations
3. **Idle Resource Detection** - Find unused resources
4. **Anomaly Detection** - Alert on unusual cost spikes
5. **Waste Analysis** - Calculate total waste across categories
