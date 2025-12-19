from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import mlflow
import mlflow.pyfunc
import numpy as np
from datetime import datetime
import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import make_asgi_app
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Model Serving", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
PREDICTIONS_TOTAL = Counter('predictions_total', 'Total predictions made', ['model', 'version'])
PREDICTION_LATENCY = Histogram('prediction_latency_seconds', 'Prediction latency', ['model'])
PREDICTION_ERRORS = Counter('prediction_errors_total', 'Prediction errors', ['model', 'error_type'])
MODELS_LOADED = Gauge('models_loaded', 'Number of models currently loaded')

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Model cache
model_cache: Dict[str, any] = {}

class PredictionRequest(BaseModel):
    model_name: str
    version: Optional[str] = "Production"
    features: List[List[float]]

class PredictionResponse(BaseModel):
    predictions: List[int]
    model_name: str
    model_version: str
    timestamp: str
    latency_ms: float

class ModelInfo(BaseModel):
    name: str
    version: str
    stage: str
    loaded: bool

def load_model(model_name: str, stage: str = "Production"):
    """Load model from MLflow registry"""
    cache_key = f"{model_name}:{stage}"
    
    if cache_key in model_cache:
        logger.info(f"Using cached model: {cache_key}")
        return model_cache[cache_key]
    
    try:
        model_uri = f"models:/{model_name}/{stage}"
        logger.info(f"Loading model from MLflow: {model_uri}")
        model = mlflow.pyfunc.load_model(model_uri)
        model_cache[cache_key] = model
        MODELS_LOADED.set(len(model_cache))
        logger.info(f"Model loaded successfully: {cache_key}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_uri}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Model not found: {model_name}/{stage}")

@app.get("/")
async def root():
    return {
        "service": "ML Model Serving",
        "version": "1.0.0",
        "mlflow_uri": MLFLOW_TRACKING_URI,
        "loaded_models": len(model_cache)
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make predictions using specified model"""
    start_time = time.time()
    
    try:
        # Load model
        model = load_model(request.model_name, request.version)
        
        # Make predictions
        features_array = np.array(request.features)
        predictions = model.predict(features_array)
        
        latency = (time.time() - start_time) * 1000
        
        # Record metrics
        PREDICTIONS_TOTAL.labels(
            model=request.model_name,
            version=request.version
        ).inc()
        PREDICTION_LATENCY.labels(model=request.model_name).observe(latency / 1000)
        
        response = PredictionResponse(
            predictions=predictions.tolist(),
            model_name=request.model_name,
            model_version=request.version,
            timestamp=datetime.now().isoformat(),
            latency_ms=round(latency, 2)
        )
        
        logger.info(f"Prediction made: {request.model_name}/{request.version}, latency: {latency:.2f}ms")
        return response
        
    except Exception as e:
        PREDICTION_ERRORS.labels(
            model=request.model_name,
            error_type=type(e).__name__
        ).inc()
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models", response_model=List[ModelInfo])
async def list_models():
    """List loaded models"""
    models = []
    for cache_key in model_cache.keys():
        name, stage = cache_key.split(':')
        models.append(ModelInfo(
            name=name,
            version=stage,
            stage=stage,
            loaded=True
        ))
    return models

@app.post("/models/reload")
async def reload_model(model_name: str, stage: str = "Production"):
    """Reload a model from registry"""
    cache_key = f"{model_name}:{stage}"
    if cache_key in model_cache:
        del model_cache[cache_key]
    
    model = load_model(model_name, stage)
    return {"status": "reloaded", "model": model_name, "stage": stage}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "loaded_models": len(model_cache),
        "mlflow_connection": "ok"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
