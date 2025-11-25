# Day 32: Log Management & Analysis

## Quick Start

1. Start all services:
   ```bash
   ./start.sh
   ```

2. Generate load:
   ```bash
   source venv/bin/activate
   python3 scripts/load_generator.py
   ```

3. View monitoring UI:
   ```bash
   cd monitoring-ui/src
   python3 -m http.server 3000
   # Open http://localhost:3000
   ```

4. Access Kibana:
   - Open http://localhost:5601
   - Go to "Discover" to view logs
   - Create index pattern: `logs-production-*`

5. Run anomaly detector:
   ```bash
   source venv/bin/activate
   python3 anomaly-detector/detector.py
   ```

6. Run tests:
   ```bash
   source venv/bin/activate
   pytest tests/test_services.py -v
   ```

7. Stop all services:
   ```bash
   ./stop.sh
   ```

## Architecture

- **Elasticsearch**: Log storage and indexing
- **Fluentd**: Log collection and processing
- **Kibana**: Log visualization and analysis
- **FastAPI Services**: Generate structured logs
- **Anomaly Detector**: Statistical anomaly detection
- **Monitoring UI**: Real-time metrics dashboard
