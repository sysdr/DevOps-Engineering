from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from datetime import datetime, timedelta
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, f1_score
import logging
from prometheus_client import Gauge, generate_latest
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Performance Tracker")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
model_accuracy = Gauge('model_accuracy', 'Model accuracy', ['model_id', 'window'])
model_precision = Gauge('model_precision', 'Model precision', ['model_id', 'window'])
model_recall = Gauge('model_recall', 'Model recall', ['model_id', 'window'])
model_f1 = Gauge('model_f1', 'Model F1 score', ['model_id', 'window'])
model_auc = Gauge('model_auc', 'Model AUC-ROC', ['model_id', 'window'])

class PerformanceTracker:
    def __init__(self):
        self.db_pool = None
        
    async def init_db(self):
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5433,
            user='postgres',
            password='postgres',
            database='monitoring'
        )
        
        # Create performance metrics table
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    model_id TEXT NOT NULL,
                    time_window TEXT NOT NULL,
                    accuracy FLOAT,
                    precision_score FLOAT,
                    recall_score FLOAT,
                    f1_score FLOAT,
                    auc_roc FLOAT,
                    sample_count INTEGER,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
    
    async def calculate_metrics(self, model_id: str, hours: int):
        async with self.db_pool.acquire() as conn:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            rows = await conn.fetch('''
                SELECT prediction, ground_truth
                FROM predictions
                WHERE model_id = $1 
                  AND timestamp > $2 
                  AND ground_truth IS NOT NULL
            ''', model_id, cutoff_time)
            
            if len(rows) < 10:
                return None
            
            y_true = [row['ground_truth'] for row in rows]
            y_pred = [row['prediction'] for row in rows]
            y_pred_binary = [1 if p > 0.5 else 0 for p in y_pred]
            
            metrics = {
                'accuracy': accuracy_score(y_true, y_pred_binary),
                'precision': precision_score(y_true, y_pred_binary, zero_division=0),
                'recall': recall_score(y_true, y_pred_binary, zero_division=0),
                'f1': f1_score(y_true, y_pred_binary, zero_division=0),
                'auc_roc': roc_auc_score(y_true, y_pred) if len(set(y_true)) > 1 else 0.0,
                'sample_count': len(rows)
            }
            
            return metrics
    
    async def track_performance(self, model_id: str = "default"):
        windows = {'1h': 1, '24h': 24, '7d': 168}
        results = {}
        
        for window_name, hours in windows.items():
            metrics = await self.calculate_metrics(model_id, hours)
            
            if metrics:
                results[window_name] = metrics
                
                # Update Prometheus metrics
                model_accuracy.labels(model_id=model_id, window=window_name).set(metrics['accuracy'])
                model_precision.labels(model_id=model_id, window=window_name).set(metrics['precision'])
                model_recall.labels(model_id=model_id, window=window_name).set(metrics['recall'])
                model_f1.labels(model_id=model_id, window=window_name).set(metrics['f1'])
                model_auc.labels(model_id=model_id, window=window_name).set(metrics['auc_roc'])
                
                # Store in database
                await self.store_metrics(model_id, window_name, metrics)
                
                logger.info(f"Tracked {window_name} performance: accuracy={metrics['accuracy']:.3f}")
        
        return results
    
    async def store_metrics(self, model_id: str, window: str, metrics: dict):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO performance_metrics 
                (timestamp, model_id, time_window, accuracy, precision_score, 
                 recall_score, f1_score, auc_roc, sample_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ''', datetime.utcnow(), model_id, window, metrics['accuracy'],
                metrics['precision'], metrics['recall'], metrics['f1'],
                metrics['auc_roc'], metrics['sample_count'])

tracker = PerformanceTracker()

@app.on_event("startup")
async def startup():
    await tracker.init_db()
    asyncio.create_task(run_periodic_tracking())
    logger.info("Performance tracker started")

async def run_periodic_tracking():
    while True:
        try:
            await tracker.track_performance()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Error in performance tracking: {e}")
            await asyncio.sleep(300)

@app.get("/performance/current")
async def get_current_performance(model_id: str = "default"):
    results = await tracker.track_performance(model_id)
    return {
        "model_id": model_id,
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": results
    }

@app.get("/performance/history")
async def get_performance_history(model_id: str = "default", hours: int = 168):
    async with tracker.db_pool.acquire() as conn:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        rows = await conn.fetch('''
            SELECT * FROM performance_metrics
            WHERE model_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
        ''', model_id, cutoff_time)
        
        return [dict(row) for row in rows]

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
