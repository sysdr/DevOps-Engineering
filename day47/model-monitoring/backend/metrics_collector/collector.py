from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import json
import asyncpg
from prometheus_client import Counter, Histogram, generate_latest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Metrics Collector")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
predictions_total = Counter('model_predictions_total', 'Total predictions', ['model_id'])
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency')

class PredictionPayload(BaseModel):
    model_id: str
    features: Dict[str, Any]
    prediction: float
    ground_truth: Optional[float] = None
    prediction_id: Optional[str] = None

class MetricsCollector:
    def __init__(self):
        self.db_pool = None
        self.predictions_buffer = []
        
    async def init_db(self):
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5433,
            user='postgres',
            password='postgres',
            database='monitoring',
            min_size=5,
            max_size=20
        )
        
        # Create tables
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    model_id TEXT NOT NULL,
                    prediction_id TEXT,
                    features JSONB NOT NULL,
                    prediction FLOAT NOT NULL,
                    ground_truth FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
                ON predictions(timestamp DESC)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_predictions_model_id 
                ON predictions(model_id)
            ''')
            
    async def store_prediction(self, payload: PredictionPayload):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO predictions 
                (timestamp, model_id, prediction_id, features, prediction, ground_truth)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', datetime.utcnow(), payload.model_id, payload.prediction_id,
                json.dumps(payload.features), payload.prediction, payload.ground_truth)
        
        predictions_total.labels(model_id=payload.model_id).inc()
        logger.info(f"Stored prediction for model {payload.model_id}")

collector = MetricsCollector()

@app.on_event("startup")
async def startup():
    await collector.init_db()
    logger.info("Metrics collector started")

@app.post("/metrics/collect")
async def collect_metrics(payload: PredictionPayload):
    try:
        await collector.store_prediction(payload)
        return {"status": "success", "prediction_id": payload.prediction_id}
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/stats")
async def get_stats():
    async with collector.db_pool.acquire() as conn:
        total = await conn.fetchval('SELECT COUNT(*) FROM predictions')
        by_model = await conn.fetch('''
            SELECT model_id, COUNT(*) as count 
            FROM predictions 
            GROUP BY model_id
        ''')
        
        return {
            "total_predictions": total,
            "by_model": [{"model_id": r['model_id'], "count": r['count']} for r in by_model]
        }

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
