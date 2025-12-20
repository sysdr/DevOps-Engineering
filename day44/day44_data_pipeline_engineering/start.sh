#!/bin/bash

echo "==================================="
echo "Starting Data Pipeline System"
echo "==================================="

# Activate virtual environment
source venv/bin/activate

# Create necessary directories
mkdir -p /tmp/pipeline_data/{raw,processed,validated,feature_store,metrics,validation}
mkdir -p /tmp/dvc_storage

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 10

# Initialize Airflow
export AIRFLOW_HOME=$(pwd)/airflow
echo "Initializing Airflow..."
airflow db init

# Create Airflow admin user
airflow users create \
    --username admin \
    --password admin123 \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com 2>/dev/null || true

# Create Kafka topics
echo "Creating Kafka topics..."
docker exec $(docker-compose ps -q kafka) kafka-topics --create --if-not-exists --topic raw-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>/dev/null || true
docker exec $(docker-compose ps -q kafka) kafka-topics --create --if-not-exists --topic validated-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>/dev/null || true
docker exec $(docker-compose ps -q kafka) kafka-topics --create --if-not-exists --topic aggregated-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>/dev/null || true

# Start Airflow scheduler and webserver in background
echo "Starting Airflow services..."
airflow scheduler > /tmp/airflow_scheduler.log 2>&1 &
airflow webserver --port 8080 > /tmp/airflow_webserver.log 2>&1 &

# Wait for Airflow to be ready
sleep 5

# Trigger initial DAG runs
echo "Triggering initial DAG runs..."
airflow dags trigger data_ingestion_dag
airflow dags trigger data_validation_dag

# Start Flink stream processor
echo "Starting Flink stream processor..."
python3 flink/stream_processor.py > /tmp/flink_processor.log 2>&1 &

# Start FastAPI backend
echo "Starting FastAPI backend..."
cd backend/app
uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
cd ../..

# Start React frontend
echo "Starting React frontend..."
cd frontend
npm install --silent
PORT=3000 npm start > /tmp/frontend.log 2>&1 &
cd ..

echo ""
echo "==================================="
echo "✓ Data Pipeline System Started!"
echo "==================================="
echo ""
echo "Services:"
echo "  - Airflow UI:        http://localhost:8080 (admin/admin123)"
echo "  - Flink Dashboard:   http://localhost:8081"
echo "  - MinIO Console:     http://localhost:9001 (minioadmin/minioadmin)"
echo "  - Backend API:       http://localhost:8000"
echo "  - Frontend:          http://localhost:3000"
echo ""
echo "To send test events:    python scripts/send_test_events.py --count 1000 --rate 50"
echo "To monitor pipeline:    ./scripts/monitor_pipeline.sh"
echo "To run tests:           pytest backend/tests/ -v"
echo "To stop services:       ./stop.sh"
echo ""
