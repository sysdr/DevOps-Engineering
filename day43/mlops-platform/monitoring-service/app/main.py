from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from prometheus_client import Gauge, Counter, generate_latest
from prometheus_client import make_asgi_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Monitoring Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
MODEL_DRIFT_SCORE = Gauge('model_drift_score', 'Model drift score', ['model'])
PREDICTION_DISTRIBUTION = Gauge('prediction_distribution', 'Prediction distribution', ['model', 'class_label'])
ERROR_RATE = Gauge('model_error_rate', 'Model error rate', ['model'])
ALERTS_TRIGGERED = Counter('monitoring_alerts_triggered_total', 'Monitoring alerts triggered', ['alert_type'])

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

class PredictionLog(BaseModel):
    model_name: str
    model_version: str
    features: List[float]
    prediction: int
    timestamp: str
    latency_ms: float

class DriftReport(BaseModel):
    model_name: str
    drift_score: float
    drift_detected: bool
    feature_drifts: Dict[str, float]
    timestamp: str

class PerformanceMetrics(BaseModel):
    model_name: str
    total_predictions: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    timestamp: str

# Storage for prediction logs and baseline
prediction_logs: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
baseline_distributions: Dict[str, np.ndarray] = {}

def calculate_drift(current_data: np.ndarray, baseline_data: np.ndarray) -> float:
    """Calculate KL divergence for drift detection"""
    try:
        # Normalize distributions
        current_hist, _ = np.histogram(current_data, bins=10, density=True)
        baseline_hist, _ = np.histogram(baseline_data, bins=10, density=True)
        
        # Add small epsilon to avoid division by zero
        epsilon = 1e-10
        current_hist = current_hist + epsilon
        baseline_hist = baseline_hist + epsilon
        
        # Normalize
        current_hist = current_hist / current_hist.sum()
        baseline_hist = baseline_hist / baseline_hist.sum()
        
        # Calculate KL divergence
        kl_div = stats.entropy(current_hist, baseline_hist)
        return float(kl_div)
    except Exception as e:
        logger.error(f"Drift calculation error: {str(e)}")
        return 0.0

@app.get("/")
async def root():
    return {
        "service": "ML Monitoring Service",
        "version": "1.0.0",
        "monitored_models": len(prediction_logs)
    }

@app.post("/log")
async def log_prediction(log: PredictionLog):
    """Log prediction for monitoring"""
    prediction_logs[log.model_name].append(log)
    
    # Update metrics
    predictions = [p.prediction for p in prediction_logs[log.model_name]]
    for class_id in set(predictions):
        count = predictions.count(class_id)
        PREDICTION_DISTRIBUTION.labels(
            model=log.model_name,
            class_label=str(class_id)
        ).set(count / len(predictions))
    
    logger.info(f"Logged prediction for {log.model_name}")
    return {"status": "logged"}

@app.post("/baseline/{model_name}")
async def set_baseline(model_name: str, features: List[List[float]]):
    """Set baseline distribution for drift detection"""
    baseline_distributions[model_name] = np.array(features)
    logger.info(f"Baseline set for {model_name}: {len(features)} samples")
    return {"status": "baseline_set", "samples": len(features)}

@app.get("/drift/{model_name}", response_model=DriftReport)
async def check_drift(model_name: str):
    """Check for model drift"""
    if model_name not in prediction_logs:
        return DriftReport(
            model_name=model_name,
            drift_score=0.0,
            drift_detected=False,
            feature_drifts={},
            timestamp=datetime.now().isoformat()
        )
    
    logs = list(prediction_logs[model_name])
    if len(logs) < 10:
        return DriftReport(
            model_name=model_name,
            drift_score=0.0,
            drift_detected=False,
            feature_drifts={},
            timestamp=datetime.now().isoformat()
        )
    
    # Get current feature distributions
    recent_features = np.array([log.features for log in logs[-100:]])
    
    # Calculate drift if baseline exists
    drift_score = 0.0
    feature_drifts = {}
    
    if model_name in baseline_distributions:
        baseline = baseline_distributions[model_name]
        
        # Overall drift
        for i in range(min(recent_features.shape[1], baseline.shape[1])):
            drift = calculate_drift(recent_features[:, i], baseline[:, i])
            feature_drifts[f"feature_{i}"] = drift
        
        drift_score = np.mean(list(feature_drifts.values()))
    
    # Update metrics
    MODEL_DRIFT_SCORE.labels(model=model_name).set(drift_score)
    
    # Alert if drift detected
    drift_detected = drift_score > 0.3
    if drift_detected:
        ALERTS_TRIGGERED.labels(alert_type='drift').inc()
        logger.warning(f"Drift detected for {model_name}: {drift_score:.3f}")
    
    return DriftReport(
        model_name=model_name,
        drift_score=round(drift_score, 4),
        drift_detected=drift_detected,
        feature_drifts=feature_drifts,
        timestamp=datetime.now().isoformat()
    )

@app.get("/performance/{model_name}", response_model=PerformanceMetrics)
async def get_performance(model_name: str):
    """Get model performance metrics"""
    if model_name not in prediction_logs:
        return PerformanceMetrics(
            model_name=model_name,
            total_predictions=0,
            avg_latency_ms=0.0,
            p95_latency_ms=0.0,
            p99_latency_ms=0.0,
            error_rate=0.0,
            timestamp=datetime.now().isoformat()
        )
    
    logs = list(prediction_logs[model_name])
    latencies = [log.latency_ms for log in logs]
    
    metrics = PerformanceMetrics(
        model_name=model_name,
        total_predictions=len(logs),
        avg_latency_ms=round(np.mean(latencies), 2) if latencies else 0.0,
        p95_latency_ms=round(np.percentile(latencies, 95), 2) if latencies else 0.0,
        p99_latency_ms=round(np.percentile(latencies, 99), 2) if latencies else 0.0,
        error_rate=0.0,  # Would calculate from error logs in production
        timestamp=datetime.now().isoformat()
    )
    
    # Update Prometheus metrics
    ERROR_RATE.labels(model=model_name).set(metrics.error_rate)
    
    return metrics

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "monitored_models": len(prediction_logs),
        "total_logs": sum(len(logs) for logs in prediction_logs.values())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
