# Day 25: Policy as Code Implementation

Complete implementation of policy enforcement system using Open Policy Agent (OPA) and Gatekeeper.

## Project Structure

```
day25-policy-as-code/
├── backend/              # Flask API server
│   ├── src/
│   │   └── api/
│   │       └── server.py
│   └── requirements.txt
├── frontend/             # Web dashboard
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── components/
│       └── styles/
├── policies/             # Gatekeeper policies
│   ├── templates/        # ConstraintTemplates
│   ├── constraints/      # Constraint instances
│   └── tests/           # Policy tests
├── k8s/                 # Sample resources
│   └── samples/
├── tests/               # Integration tests
└── docker-compose.yml   # Container orchestration
```

## Quick Start

### Without Docker

```bash
cd day25-policy-as-code
./start.sh
```

Access:
- Dashboard: http://localhost:3000
- API: http://localhost:5000

### With Docker

```bash
docker-compose up --build
```

## Features

- Real-time policy violation monitoring
- Automated remediation workflows
- Compliance metrics and trends
- Policy testing with OPA test framework
- RESTful API for integration

## API Endpoints

- `GET /health` - Health check
- `GET /api/policies` - List active policies
- `GET /api/violations` - Get violations with filtering
- `POST /api/violations/{id}/remediate` - Trigger remediation
- `GET /api/compliance/metrics` - Compliance statistics
- `GET /api/compliance/trends` - Historical trends

## Testing

```bash
cd backend
source venv/bin/activate
pytest ../tests/ -v
```

## Cleanup

```bash
./stop.sh
```

## Next Steps

Deploy Gatekeeper to actual Kubernetes cluster:

```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.16/deploy/gatekeeper.yaml
kubectl apply -f policies/templates/
kubectl apply -f policies/constraints/
```
