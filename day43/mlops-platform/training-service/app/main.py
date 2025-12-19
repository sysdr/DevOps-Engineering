from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pandas as pd
import numpy as np
from datetime import datetime
import os
import uuid
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import make_asgi_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Training Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
TRAINING_JOBS = Counter('training_jobs_total', 'Total training jobs submitted', ['status'])
TRAINING_DURATION = Histogram('training_duration_seconds', 'Training job duration')
ACTIVE_JOBS = Gauge('active_training_jobs', 'Currently active training jobs')
MODELS_TRAINED = Counter('models_trained_total', 'Total models trained', ['model_type'])

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
# Configure S3/MinIO credentials for MLflow artifacts
os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.getenv('MLFLOW_S3_ENDPOINT_URL', os.getenv('MINIO_URL', 'http://minio:9000'))
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID', os.getenv('MINIO_ACCESS_KEY', 'minioadmin'))
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY', os.getenv('MINIO_SECRET_KEY', 'minioadmin'))

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

class TrainingRequest(BaseModel):
    experiment_name: str
    model_type: str  # 'random_forest', 'gradient_boosting', 'logistic_regression'
    hyperparameters: Dict[str, Any]
    dataset_config: Dict[str, Any]
    tags: Optional[Dict[str, str]] = {}

class TrainingJob(BaseModel):
    job_id: str
    status: str
    experiment_id: Optional[str] = None
    run_id: Optional[str] = None
    model_uri: Optional[str] = None
    metrics: Optional[Dict[str, float]] = {}
    created_at: str
    completed_at: Optional[str] = None

# In-memory job storage (in production, use Redis/DB)
jobs_store: Dict[str, TrainingJob] = {}

def generate_synthetic_data(n_samples: int = 1000, n_features: int = 20):
    """Generate synthetic classification dataset"""
    np.random.seed(42)
    X = np.random.randn(n_samples, n_features)
    # Create non-linear decision boundary
    y = (X[:, 0] + X[:, 1]**2 + np.random.randn(n_samples) * 0.5 > 0).astype(int)
    return X, y

def train_model(job_id: str, request: TrainingRequest):
    """Execute model training with MLflow tracking"""
    ACTIVE_JOBS.inc()
    start_time = datetime.now()
    
    try:
        # Create or get experiment
        experiment = mlflow.get_experiment_by_name(request.experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(request.experiment_name)
        else:
            experiment_id = experiment.experiment_id
        
        jobs_store[job_id].experiment_id = experiment_id
        
        # Start MLflow run
        with mlflow.start_run(experiment_id=experiment_id) as run:
            run_id = run.info.run_id
            jobs_store[job_id].run_id = run_id
            
            # Log parameters
            mlflow.log_params(request.hyperparameters)
            mlflow.set_tags({**request.tags, "job_id": job_id})
            
            # Generate or load data
            logger.info(f"Generating training data for job {job_id}")
            X, y = generate_synthetic_data(
                n_samples=request.dataset_config.get('n_samples', 1000),
                n_features=request.dataset_config.get('n_features', 20)
            )
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model based on type
            logger.info(f"Training {request.model_type} model")
            if request.model_type == 'random_forest':
                model = RandomForestClassifier(**request.hyperparameters)
            elif request.model_type == 'gradient_boosting':
                model = GradientBoostingClassifier(**request.hyperparameters)
            elif request.model_type == 'logistic_regression':
                model = LogisticRegression(**request.hyperparameters)
            else:
                raise ValueError(f"Unknown model type: {request.model_type}")
            
            model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test)
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted'),
                'recall': recall_score(y_test, y_pred, average='weighted'),
                'f1_score': f1_score(y_test, y_pred, average='weighted')
            }
            
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Log model
            model_uri = mlflow.sklearn.log_model(
                model, 
                "model",
                registered_model_name=f"{request.experiment_name}_{request.model_type}"
            ).model_uri
            
            # Update job status
            jobs_store[job_id].status = 'completed'
            jobs_store[job_id].model_uri = model_uri
            jobs_store[job_id].metrics = metrics
            jobs_store[job_id].completed_at = datetime.now().isoformat()
            
            duration = (datetime.now() - start_time).total_seconds()
            TRAINING_DURATION.observe(duration)
            TRAINING_JOBS.labels(status='success').inc()
            MODELS_TRAINED.labels(model_type=request.model_type).inc()
            
            logger.info(f"Job {job_id} completed successfully. Metrics: {metrics}")
            
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        jobs_store[job_id].status = 'failed'
        jobs_store[job_id].completed_at = datetime.now().isoformat()
        TRAINING_JOBS.labels(status='failed').inc()
    finally:
        ACTIVE_JOBS.dec()

@app.get("/")
async def root():
    return {
        "service": "ML Training Service",
        "version": "1.0.0",
        "mlflow_uri": MLFLOW_TRACKING_URI
    }

@app.post("/train", response_model=TrainingJob)
async def submit_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Submit a new training job"""
    job_id = str(uuid.uuid4())
    
    job = TrainingJob(
        job_id=job_id,
        status='submitted',
        created_at=datetime.now().isoformat()
    )
    jobs_store[job_id] = job
    
    # Start training in background
    background_tasks.add_task(train_model, job_id, request)
    
    TRAINING_JOBS.labels(status='submitted').inc()
    logger.info(f"Training job submitted: {job_id}")
    
    return job

@app.get("/jobs/{job_id}", response_model=TrainingJob)
async def get_job_status(job_id: str):
    """Get status of a training job"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_store[job_id]

@app.get("/jobs", response_model=List[TrainingJob])
async def list_jobs(limit: int = 10):
    """List recent training jobs"""
    jobs = list(jobs_store.values())
    return sorted(jobs, key=lambda x: x.created_at, reverse=True)[:limit]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_jobs": len([j for j in jobs_store.values() if j.status == 'submitted'])}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
