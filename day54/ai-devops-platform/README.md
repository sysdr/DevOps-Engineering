# Day 54: AI-Powered DevOps Tools

Production-grade AI DevOps platform with intelligent code analysis, log monitoring, incident management, and automated documentation.

## Features

- **AI Code Analyzer**: Security scanning, complexity analysis, and quality checks
- **Intelligent Log Analyzer**: Real-time anomaly detection with ML
- **AI Incident Manager**: Alert correlation and root cause analysis
- **Doc Generator**: Automated documentation from source code

## Quick Start

### Using Start Script (Recommended)
```bash
./start.sh
```

Access dashboard at http://localhost:3000

### Using Docker Compose
```bash
docker-compose up -d
```

## Testing

```bash
source venv/bin/activate
python tests/test_all.py
```

## Stopping Services

```bash
./stop.sh
```

## Architecture

- **Backend**: Python 3.11 + FastAPI
- **Frontend**: React
- **ML**: scikit-learn for anomaly detection
- **Ports**: 8001-8004 (services), 3000 (dashboard)

## API Documentation

- Code Analyzer: http://localhost:8001/docs
- Log Analyzer: http://localhost:8002/docs
- Incident Manager: http://localhost:8003/docs
- Doc Generator: http://localhost:8004/docs
