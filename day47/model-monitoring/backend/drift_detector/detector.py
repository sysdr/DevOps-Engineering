from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import json
import asyncio
from typing import Dict, List
import logging
from prometheus_client import Gauge, generate_latest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Drift Detector")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
drift_score = Gauge('model_drift_score', 'Drift detection score', ['model_id', 'feature'])
drift_alerts = Gauge('model_drift_alerts', 'Active drift alerts', ['model_id'])

class DriftDetector:
    def __init__(self):
        self.db_pool = None
        self.reference_distributions = {}
        
    async def init_db(self):
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5433,
            user='postgres',
            password='postgres',
            database='monitoring'
        )
        
        # Create drift events table
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS drift_events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    model_id TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    drift_score FLOAT NOT NULL,
                    p_value FLOAT NOT NULL,
                    test_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
    
    def load_reference_distributions(self, model_id: str = "default"):
        # Simulate reference distributions (in production, load from training data)
        self.reference_distributions[model_id] = {
            'amount': np.random.normal(100, 30, 10000),
            'frequency': np.random.normal(5, 2, 10000),
            'recency': np.random.exponential(10, 10000),
        }
        logger.info(f"Loaded reference distributions for model {model_id}")
    
    async def get_recent_feature_values(self, model_id: str, feature_name: str, hours: int = 1):
        async with self.db_pool.acquire() as conn:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            rows = await conn.fetch('''
                SELECT features->$1 as feature_value
                FROM predictions
                WHERE model_id = $2 AND timestamp > $3
            ''', feature_name, model_id, cutoff_time)
            
            values = []
            for row in rows:
                try:
                    val = float(row['feature_value'])
                    if not np.isnan(val):
                        values.append(val)
                except (ValueError, TypeError):
                    continue
            
            return np.array(values)
    
    def detect_numeric_drift(self, feature_name: str, recent_values: np.ndarray, 
                            reference_values: np.ndarray) -> Dict:
        if len(recent_values) < 30:
            return {"drift_detected": False, "reason": "insufficient_data"}
        
        # Kolmogorov-Smirnov test
        ks_stat, p_value = stats.ks_2samp(recent_values, reference_values)
        
        drift_detected = bool(p_value < 0.05)  # Convert numpy.bool_ to Python bool
        severity = "critical" if p_value < 0.01 else "warning" if p_value < 0.05 else "normal"
        
        return {
            "drift_detected": drift_detected,
            "ks_statistic": float(ks_stat),
            "p_value": float(p_value),
            "test_type": "ks_2samp",
            "severity": severity,
            "recent_mean": float(np.mean(recent_values)),
            "recent_std": float(np.std(recent_values)),
            "reference_mean": float(np.mean(reference_values)),
            "reference_std": float(np.std(reference_values))
        }
    
    async def run_drift_detection(self, model_id: str = "default"):
        if model_id not in self.reference_distributions:
            self.load_reference_distributions(model_id)
        
        results = {}
        for feature_name in self.reference_distributions[model_id].keys():
            recent_values = await self.get_recent_feature_values(model_id, feature_name)
            
            if len(recent_values) > 0:
                reference_values = self.reference_distributions[model_id][feature_name]
                drift_result = self.detect_numeric_drift(feature_name, recent_values, reference_values)
                results[feature_name] = drift_result
                
                # Update Prometheus metrics
                drift_score.labels(model_id=model_id, feature=feature_name).set(
                    drift_result.get('ks_statistic', 0)
                )
                
                # Store drift events
                if drift_result['drift_detected']:
                    await self.store_drift_event(model_id, feature_name, drift_result)
                    logger.warning(f"Drift detected in {feature_name}: p-value={drift_result['p_value']:.4f}")
        
        active_alerts = sum(1 for r in results.values() if r.get('drift_detected', False))
        drift_alerts.labels(model_id=model_id).set(active_alerts)
        
        return results
    
    async def store_drift_event(self, model_id: str, feature_name: str, drift_result: Dict):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO drift_events 
                (timestamp, model_id, feature_name, drift_score, p_value, test_type, severity)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', datetime.utcnow(), model_id, feature_name, 
                drift_result['ks_statistic'], drift_result['p_value'],
                drift_result['test_type'], drift_result['severity'])

detector = DriftDetector()

@app.on_event("startup")
async def startup():
    await detector.init_db()
    detector.load_reference_distributions()
    
    # Start background drift detection
    asyncio.create_task(run_periodic_detection())
    logger.info("Drift detector started")

async def run_periodic_detection():
    while True:
        try:
            await detector.run_drift_detection()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Error in drift detection: {e}")
            await asyncio.sleep(60)

@app.get("/drift/status")
async def get_drift_status(model_id: str = "default"):
    results = await detector.run_drift_detection(model_id)
    return {
        "model_id": model_id,
        "timestamp": datetime.utcnow().isoformat(),
        "features": results
    }

@app.get("/drift/history")
async def get_drift_history(model_id: str = "default", hours: int = 24):
    async with detector.db_pool.acquire() as conn:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        rows = await conn.fetch('''
            SELECT * FROM drift_events
            WHERE model_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
            LIMIT 100
        ''', model_id, cutoff_time)
        
        return [dict(row) for row in rows]

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
