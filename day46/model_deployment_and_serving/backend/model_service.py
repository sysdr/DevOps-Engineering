from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import numpy as np
import pickle
import time
import json
from datetime import datetime
import asyncio
from collections import defaultdict
import redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response
import os

app = FastAPI(title="Model Serving Platform")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
PREDICTION_COUNTER = Counter('model_predictions_total', 'Total predictions', ['model_version', 'status'])
PREDICTION_LATENCY = Histogram('model_prediction_latency_seconds', 'Prediction latency', ['model_version'])
ACTIVE_MODELS = Gauge('active_models', 'Number of active models')
REQUEST_RATE = Counter('request_rate_total', 'Request rate', ['endpoint'])

# Redis for caching and metrics
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=1)

# Model registry
models = {}
model_metadata = {}
traffic_split = {"v1": 90, "v2": 10}  # A/B testing traffic split
prediction_cache = {}

class PredictionRequest(BaseModel):
    instances: List[List[float]]
    version: Optional[str] = None

class PredictionResponse(BaseModel):
    predictions: List[int]
    model_version: str
    latency_ms: float
    timestamp: str

class ModelMetadata(BaseModel):
    version: str
    framework: str
    created: str
    size_mb: float
    quantized: bool
    accuracy: float

class TrafficSplitConfig(BaseModel):
    v1: int
    v2: int

class ModelMetrics(BaseModel):
    version: str
    total_predictions: int
    avg_latency_ms: float
    error_rate: float
    last_prediction: str

# Simple Iris classifier model
class SimpleIrisModel:
    def __init__(self, version="v1", quantized=False):
        self.version = version
        self.quantized = quantized
        # Simple decision boundaries for Iris dataset
        self.boundaries = np.array([
            [5.0, 3.0],  # Setosa
            [6.0, 2.8],  # Versicolor
            [7.0, 3.0]   # Virginica
        ])
        
    def predict(self, X):
        """Simple classification based on sepal length and width"""
        predictions = []
        for features in X:
            sepal_length, sepal_width = features[0], features[1]
            
            # Simple decision tree logic
            if sepal_length < 5.5:
                predictions.append(0)  # Setosa
            elif sepal_length < 6.5:
                predictions.append(1)  # Versicolor
            else:
                predictions.append(2)  # Virginica
        
        return np.array(predictions)
    
    def predict_proba(self, X):
        """Return probabilities"""
        preds = self.predict(X)
        proba = np.zeros((len(preds), 3))
        for i, pred in enumerate(preds):
            proba[i, pred] = 0.95
            proba[i, (pred + 1) % 3] = 0.03
            proba[i, (pred + 2) % 3] = 0.02
        return proba

def load_models():
    """Load model versions"""
    global models, model_metadata
    
    # Load v1 (baseline)
    models["v1"] = SimpleIrisModel(version="v1", quantized=False)
    model_metadata["v1"] = {
        "version": "v1",
        "framework": "scikit-learn",
        "created": "2025-01-01T00:00:00Z",
        "size_mb": 0.5,
        "quantized": False,
        "accuracy": 0.96
    }
    
    # Load v2 (improved version for A/B testing)
    models["v2"] = SimpleIrisModel(version="v2", quantized=False)
    model_metadata["v2"] = {
        "version": "v2",
        "framework": "scikit-learn",
        "created": "2025-01-15T00:00:00Z",
        "size_mb": 0.5,
        "quantized": False,
        "accuracy": 0.97
    }
    
    # Load v2-quantized
    models["v2-quantized"] = SimpleIrisModel(version="v2-quantized", quantized=True)
    model_metadata["v2-quantized"] = {
        "version": "v2-quantized",
        "framework": "scikit-learn",
        "created": "2025-01-15T00:00:00Z",
        "size_mb": 0.125,  # 4x smaller
        "quantized": True,
        "accuracy": 0.96
    }
    
    ACTIVE_MODELS.set(len(models))
    print(f"Loaded {len(models)} model versions")

def select_model_version(requested_version: Optional[str] = None) -> str:
    """Select model version based on traffic split or explicit request"""
    if requested_version and requested_version in models:
        return requested_version
    
    # Random selection based on traffic split
    rand = np.random.randint(0, 100)
    cumulative = 0
    for version, percentage in traffic_split.items():
        cumulative += percentage
        if rand < cumulative:
            return version
    
    return "v1"  # Default fallback

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    load_models()
    print("Model serving platform started")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": len(models),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to prevent 404 errors"""
    return Response(status_code=204)

@app.post("/v1/models/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Main prediction endpoint with A/B testing"""
    REQUEST_RATE.labels(endpoint="predict").inc()
    
    start_time = time.time()
    
    try:
        # Select model version
        version = select_model_version(request.version)
        model = models[version]
        
        # Convert to numpy array
        X = np.array(request.instances)
        
        # Check cache
        cache_key = f"prediction:{version}:{hash(X.tobytes())}"
        cached_result = prediction_cache.get(cache_key)
        
        if cached_result:
            latency_ms = (time.time() - start_time) * 1000
            return PredictionResponse(
                predictions=cached_result,
                model_version=version,
                latency_ms=latency_ms,
                timestamp=datetime.now().isoformat()
            )
        
        # Make prediction
        predictions = model.predict(X).tolist()
        
        # Cache result
        prediction_cache[cache_key] = predictions
        
        # Record metrics
        latency = time.time() - start_time
        latency_ms = latency * 1000
        
        PREDICTION_COUNTER.labels(model_version=version, status="success").inc()
        PREDICTION_LATENCY.labels(model_version=version).observe(latency)
        
        # Store metrics in Redis
        try:
            redis_client.hincrby(f"model_metrics:{version}", "total_predictions", 1)
            redis_client.hset(f"model_metrics:{version}", "last_prediction", datetime.now().isoformat())
            redis_client.lpush(f"latencies:{version}", latency_ms)
            redis_client.ltrim(f"latencies:{version}", 0, 999)  # Keep last 1000
        except:
            pass  # Redis optional
        
        return PredictionResponse(
            predictions=predictions,
            model_version=version,
            latency_ms=latency_ms,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        PREDICTION_COUNTER.labels(model_version="unknown", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List all available model versions"""
    return {
        "models": [
            {**metadata, "status": "ready"}
            for version, metadata in model_metadata.items()
        ]
    }

@app.get("/v1/models/{version}/metadata")
async def get_model_metadata(version: str):
    """Get metadata for specific model version"""
    if version not in model_metadata:
        raise HTTPException(status_code=404, detail="Model version not found")
    
    return model_metadata[version]

@app.get("/v1/traffic-split")
async def get_traffic_split():
    """Get current traffic split configuration"""
    return traffic_split

@app.post("/v1/traffic-split")
async def update_traffic_split(config: TrafficSplitConfig):
    """Update traffic split for A/B testing"""
    global traffic_split
    
    total = config.v1 + config.v2
    if total != 100:
        raise HTTPException(status_code=400, detail="Traffic split must sum to 100")
    
    traffic_split = {"v1": config.v1, "v2": config.v2}
    
    return {
        "status": "updated",
        "traffic_split": traffic_split,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/metrics/{version}")
async def get_model_metrics(version: str):
    """Get metrics for specific model version"""
    if version not in models:
        raise HTTPException(status_code=404, detail="Model version not found")
    
    try:
        total_predictions = int(redis_client.hget(f"model_metrics:{version}", "total_predictions") or 0)
        last_prediction = redis_client.hget(f"model_metrics:{version}", "last_prediction") or "N/A"
        
        # Calculate average latency
        latencies = redis_client.lrange(f"latencies:{version}", 0, -1)
        latencies = [float(l) for l in latencies]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return ModelMetrics(
            version=version,
            total_predictions=total_predictions,
            avg_latency_ms=round(avg_latency, 2),
            error_rate=0.0,  # Simplified
            last_prediction=last_prediction
        )
    except:
        # If Redis unavailable, return defaults
        return ModelMetrics(
            version=version,
            total_predictions=0,
            avg_latency_ms=0.0,
            error_rate=0.0,
            last_prediction="N/A"
        )

@app.get("/v1/compare-models")
async def compare_models():
    """Compare metrics across all model versions"""
    comparison = {}
    
    for version in models.keys():
        try:
            metrics = await get_model_metrics(version)
            comparison[version] = {
                "total_predictions": metrics.total_predictions,
                "avg_latency_ms": metrics.avg_latency_ms,
                "accuracy": model_metadata[version]["accuracy"],
                "size_mb": model_metadata[version]["size_mb"]
            }
        except:
            continue
    
    return {"comparison": comparison}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
