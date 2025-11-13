# Day 27: Disaster Recovery & Business Continuity

## Quick Start

### Without Docker
```bash
./start.sh
```

### With Docker
```bash
docker-compose up --build
```

## Access
- Dashboard: http://localhost:3000
- API: http://localhost:8000

## Testing
```bash
cd backend
source venv/bin/activate
python ../tests/test_backup_manager.py
```

## Features
- Automated backup creation and management
- Cross-region replication monitoring
- One-click failover capability
- RTO/RPO metrics tracking
- Modern web dashboard

## Stopping
```bash
./stop.sh
```
or
```bash
docker-compose down
```
