import os
import mlflow
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from prometheus_client import start_http_server
import time

# Prometheus metrics
EXPERIMENTS_CREATED = Counter('mlflow_experiments_created_total', 'Total experiments created')
RUNS_LOGGED = Counter('mlflow_runs_logged_total', 'Total runs logged')
MODELS_REGISTERED = Counter('mlflow_models_registered_total', 'Total models registered')
API_REQUEST_DURATION = Histogram('mlflow_api_request_duration_seconds', 'API request duration')

def setup_mlflow():
    """Configure MLflow server with PostgreSQL backend and MinIO artifacts"""
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.getenv('MINIO_URL', 'http://minio:9000')
    os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    
    print("MLflow server configured with:")
    print(f"- Backend: {os.getenv('BACKEND_STORE_URI', 'sqlite:///mlflow.db')}")
    print(f"- Artifacts: {os.getenv('ARTIFACT_ROOT', './mlflow-artifacts')}")
    print(f"- Host: 0.0.0.0:5000")

if __name__ == "__main__":
    setup_mlflow()
    # Start Prometheus metrics endpoint
    start_http_server(8001)
    print("Prometheus metrics available at :8001/metrics")
    
    # MLflow server will be started by gunicorn command
    print("MLflow server ready to start...")
