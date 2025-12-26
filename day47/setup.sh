#!/bin/bash

set -e

echo "=== Day 47: Model Monitoring & Observability Platform Setup ==="
echo "Building production-grade ML monitoring system..."

# Create project structure
echo "Creating project structure..."
mkdir -p model-monitoring/{backend,frontend,tests,docker,config,data}
mkdir -p model-monitoring/backend/{metrics_collector,drift_detector,performance_tracker,explainability,fairness_monitor,models}
mkdir -p model-monitoring/frontend/{src,public}
mkdir -p model-monitoring/frontend/src/{components,services,utils}
mkdir -p model-monitoring/tests/{unit,integration}
mkdir -p model-monitoring/data/{reference,models}

cd model-monitoring

# Create backend metrics collector service
echo "Creating metrics collector service..."
cat > backend/metrics_collector/collector.py << 'EOF'
from fastapi import FastAPI, HTTPException
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
            port=5432,
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
EOF

# Create drift detector
echo "Creating drift detector..."
cat > backend/drift_detector/detector.py << 'EOF'
from fastapi import FastAPI
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
            port=5432,
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
        
        drift_detected = p_value < 0.05
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
EOF

# Create performance tracker
echo "Creating performance tracker..."
cat > backend/performance_tracker/tracker.py << 'EOF'
from fastapi import FastAPI
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
            port=5432,
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
EOF

# Create explainability service
echo "Creating explainability service..."
cat > backend/explainability/service.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
import numpy as np
import json
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Explainability Service")

class ExplanationRequest(BaseModel):
    prediction_id: str
    model_id: str = "default"

class ExplainabilityService:
    def __init__(self):
        self.db_pool = None
        self.model = None
        
    async def init_db(self):
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='monitoring'
        )
        
        # Create explanations table
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS explanations (
                    id SERIAL PRIMARY KEY,
                    prediction_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    explanation_type TEXT NOT NULL,
                    feature_importance JSONB NOT NULL,
                    base_value FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
    
    def calculate_shap_values(self, features: Dict) -> Dict:
        # Simplified SHAP calculation (in production, use actual SHAP library)
        feature_values = {k: float(v) if isinstance(v, (int, float)) else 0.0 
                         for k, v in features.items()}
        
        # Simulate SHAP value calculation
        base_value = 0.5
        shap_values = {}
        
        for feature_name, feature_value in feature_values.items():
            # Simple contribution calculation
            contribution = (feature_value / 100.0) * np.random.uniform(-0.2, 0.2)
            shap_values[feature_name] = contribution
        
        return {
            "shap_values": shap_values,
            "base_value": base_value,
            "predicted_value": base_value + sum(shap_values.values())
        }
    
    def calculate_lime_explanation(self, features: Dict) -> Dict:
        # Simplified LIME explanation
        feature_values = {k: float(v) if isinstance(v, (int, float)) else 0.0 
                         for k, v in features.items()}
        
        # Simulate local linear approximation
        weights = {}
        for feature_name, feature_value in feature_values.items():
            weight = np.random.uniform(-0.5, 0.5)
            weights[feature_name] = weight
        
        intercept = 0.5
        prediction = intercept + sum(w * feature_values[f] / 100.0 
                                    for f, w in weights.items())
        
        return {
            "weights": weights,
            "intercept": intercept,
            "local_prediction": prediction,
            "r2_score": 0.85
        }
    
    async def get_prediction_features(self, prediction_id: str):
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT features, prediction
                FROM predictions
                WHERE prediction_id = $1
                LIMIT 1
            ''', prediction_id)
            
            if not row:
                raise ValueError(f"Prediction {prediction_id} not found")
            
            return json.loads(row['features']), row['prediction']
    
    async def generate_explanation(self, prediction_id: str, model_id: str, 
                                   explanation_type: str = "shap"):
        features, prediction = await self.get_prediction_features(prediction_id)
        
        if explanation_type == "shap":
            explanation = self.calculate_shap_values(features)
        elif explanation_type == "lime":
            explanation = self.calculate_lime_explanation(features)
        else:
            raise ValueError(f"Unknown explanation type: {explanation_type}")
        
        # Store explanation
        await self.store_explanation(prediction_id, model_id, explanation_type, explanation)
        
        return explanation
    
    async def store_explanation(self, prediction_id: str, model_id: str, 
                               explanation_type: str, explanation: Dict):
        async with self.db_pool.acquire() as conn:
            feature_importance = explanation.get('shap_values') or explanation.get('weights')
            base_value = explanation.get('base_value') or explanation.get('intercept')
            
            await conn.execute('''
                INSERT INTO explanations 
                (prediction_id, model_id, explanation_type, feature_importance, base_value)
                VALUES ($1, $2, $3, $4, $5)
            ''', prediction_id, model_id, explanation_type, 
                json.dumps(feature_importance), base_value)

service = ExplainabilityService()

@app.on_event("startup")
async def startup():
    await service.init_db()
    logger.info("Explainability service started")

@app.post("/explain/shap")
async def generate_shap_explanation(request: ExplanationRequest):
    try:
        explanation = await service.generate_explanation(
            request.prediction_id, request.model_id, "shap"
        )
        return {
            "prediction_id": request.prediction_id,
            "explanation_type": "shap",
            "explanation": explanation
        }
    except Exception as e:
        logger.error(f"Error generating SHAP explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain/lime")
async def generate_lime_explanation(request: ExplanationRequest):
    try:
        explanation = await service.generate_explanation(
            request.prediction_id, request.model_id, "lime"
        )
        return {
            "prediction_id": request.prediction_id,
            "explanation_type": "lime",
            "explanation": explanation
        }
    except Exception as e:
        logger.error(f"Error generating LIME explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/explain/history/{prediction_id}")
async def get_explanation_history(prediction_id: str):
    async with service.db_pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT * FROM explanations
            WHERE prediction_id = $1
            ORDER BY created_at DESC
        ''', prediction_id)
        
        return [dict(row) for row in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
EOF

# Create fairness monitor
echo "Creating fairness monitor..."
cat > backend/fairness_monitor/monitor.py << 'EOF'
from fastapi import FastAPI
import asyncpg
from datetime import datetime, timedelta
import numpy as np
from sklearn.metrics import confusion_matrix
import json
import logging
from prometheus_client import Gauge, generate_latest
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fairness Monitor")

# Prometheus metrics
demographic_parity = Gauge('model_demographic_parity', 'Demographic parity disparity', 
                          ['model_id', 'protected_attr'])
equalized_odds_tpr = Gauge('model_equalized_odds_tpr', 'TPR disparity', 
                           ['model_id', 'protected_attr'])
equalized_odds_fpr = Gauge('model_equalized_odds_fpr', 'FPR disparity', 
                           ['model_id', 'protected_attr'])

class FairnessMonitor:
    def __init__(self):
        self.db_pool = None
        self.protected_attributes = ['gender', 'age_group', 'ethnicity']
        
    async def init_db(self):
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='monitoring'
        )
        
        # Create fairness metrics table
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS fairness_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    model_id TEXT NOT NULL,
                    protected_attribute TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    groups JSONB NOT NULL,
                    disparity FLOAT NOT NULL,
                    alert_triggered BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
    
    async def get_predictions_by_group(self, model_id: str, protected_attr: str, hours: int = 24):
        # Simulate getting predictions with protected attributes
        # In production, this would join with user metadata table
        async with self.db_pool.acquire() as conn:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            rows = await conn.fetch('''
                SELECT prediction, ground_truth
                FROM predictions
                WHERE model_id = $1 AND timestamp > $2 AND ground_truth IS NOT NULL
            ''', model_id, cutoff_time)
            
            # Simulate group assignments for demonstration
            np.random.seed(42)
            groups = {}
            for row in rows:
                group = np.random.choice(['group_a', 'group_b'], p=[0.6, 0.4])
                if group not in groups:
                    groups[group] = {'predictions': [], 'ground_truth': []}
                groups[group]['predictions'].append(row['prediction'])
                groups[group]['ground_truth'].append(row['ground_truth'])
            
            return groups
    
    def calculate_demographic_parity(self, groups: dict) -> dict:
        approval_rates = {}
        for group_name, data in groups.items():
            predictions = np.array(data['predictions'])
            approval_rate = (predictions > 0.5).mean()
            approval_rates[group_name] = float(approval_rate)
        
        if len(approval_rates) < 2:
            return {"disparity": 0.0, "groups": approval_rates}
        
        disparity = max(approval_rates.values()) - min(approval_rates.values())
        
        return {
            "disparity": float(disparity),
            "groups": approval_rates
        }
    
    def calculate_equalized_odds(self, groups: dict) -> dict:
        metrics = {}
        for group_name, data in groups.items():
            if len(data['ground_truth']) < 10:
                continue
                
            y_true = np.array(data['ground_truth'])
            y_pred = (np.array(data['predictions']) > 0.5).astype(int)
            
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            
            metrics[group_name] = {
                "tpr": float(tpr),
                "fpr": float(fpr)
            }
        
        if len(metrics) < 2:
            return {"tpr_disparity": 0.0, "fpr_disparity": 0.0, "groups": metrics}
        
        tprs = [m['tpr'] for m in metrics.values()]
        fprs = [m['fpr'] for m in metrics.values()]
        
        return {
            "tpr_disparity": float(max(tprs) - min(tprs)),
            "fpr_disparity": float(max(fprs) - min(fprs)),
            "groups": metrics
        }
    
    async def monitor_fairness(self, model_id: str = "default"):
        results = {}
        
        for protected_attr in self.protected_attributes:
            groups = await self.get_predictions_by_group(model_id, protected_attr)
            
            if not groups:
                continue
            
            # Calculate demographic parity
            dp_result = self.calculate_demographic_parity(groups)
            results[f"{protected_attr}_demographic_parity"] = dp_result
            
            # Calculate equalized odds
            eo_result = self.calculate_equalized_odds(groups)
            results[f"{protected_attr}_equalized_odds"] = eo_result
            
            # Update Prometheus metrics
            demographic_parity.labels(
                model_id=model_id, 
                protected_attr=protected_attr
            ).set(dp_result['disparity'])
            
            equalized_odds_tpr.labels(
                model_id=model_id, 
                protected_attr=protected_attr
            ).set(eo_result['tpr_disparity'])
            
            equalized_odds_fpr.labels(
                model_id=model_id, 
                protected_attr=protected_attr
            ).set(eo_result['fpr_disparity'])
            
            # Store metrics and check for alerts
            alert_triggered = dp_result['disparity'] > 0.1 or eo_result['tpr_disparity'] > 0.1
            
            await self.store_fairness_metrics(
                model_id, protected_attr, "demographic_parity",
                dp_result['groups'], dp_result['disparity'], alert_triggered
            )
            
            if alert_triggered:
                logger.warning(
                    f"Fairness alert for {protected_attr}: "
                    f"DP disparity={dp_result['disparity']:.3f}, "
                    f"TPR disparity={eo_result['tpr_disparity']:.3f}"
                )
        
        return results
    
    async def store_fairness_metrics(self, model_id: str, protected_attr: str,
                                     metric_type: str, groups: dict, disparity: float,
                                     alert_triggered: bool):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO fairness_metrics 
                (timestamp, model_id, protected_attribute, metric_type, 
                 groups, disparity, alert_triggered)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', datetime.utcnow(), model_id, protected_attr, metric_type,
                json.dumps(groups), disparity, alert_triggered)

monitor = FairnessMonitor()

@app.on_event("startup")
async def startup():
    await monitor.init_db()
    asyncio.create_task(run_periodic_monitoring())
    logger.info("Fairness monitor started")

async def run_periodic_monitoring():
    while True:
        try:
            await monitor.monitor_fairness()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Error in fairness monitoring: {e}")
            await asyncio.sleep(300)

@app.get("/fairness/current")
async def get_current_fairness(model_id: str = "default"):
    results = await monitor.monitor_fairness(model_id)
    return {
        "model_id": model_id,
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": results
    }

@app.get("/fairness/alerts")
async def get_fairness_alerts(model_id: str = "default", hours: int = 24):
    async with monitor.db_pool.acquire() as conn:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        rows = await conn.fetch('''
            SELECT * FROM fairness_metrics
            WHERE model_id = $1 AND timestamp > $2 AND alert_triggered = TRUE
            ORDER BY timestamp DESC
        ''', model_id, cutoff_time)
        
        return [dict(row) for row in rows]

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
EOF

# Create React dashboard
echo "Creating React monitoring dashboard..."
cat > frontend/package.json << 'EOF'
{
  "name": "model-monitoring-dashboard",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "recharts": "^2.10.0",
    "axios": "^1.6.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": ["react-app"]
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}
EOF

cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Model Monitoring Dashboard</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

cat > frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

cat > frontend/src/index.css << 'EOF'
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  min-height: 100vh;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New', monospace;
}
EOF

cat > frontend/src/App.js << 'EOF'
import React, { useState, useEffect } from 'react';
import './App.css';
import MetricsCollectorPanel from './components/MetricsCollectorPanel';
import DriftDetectionPanel from './components/DriftDetectionPanel';
import PerformancePanel from './components/PerformancePanel';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import FairnessPanel from './components/FairnessPanel';

function App() {
  const [activeTab, setActiveTab] = useState('metrics');
  const [systemStatus, setSystemStatus] = useState('healthy');

  useEffect(() => {
    const interval = setInterval(() => {
      fetch('http://localhost:8000/metrics/stats')
        .then(res => res.json())
        .then(data => {
          if (data.total_predictions > 0) {
            setSystemStatus('healthy');
          }
        })
        .catch(() => setSystemStatus('degraded'));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>🎯 Model Monitoring & Observability Platform</h1>
          <div className="system-status">
            <span className={`status-indicator ${systemStatus}`}></span>
            <span>System {systemStatus}</span>
          </div>
        </div>
        <nav className="nav-tabs">
          <button 
            className={activeTab === 'metrics' ? 'active' : ''}
            onClick={() => setActiveTab('metrics')}
          >
            📊 Metrics Collection
          </button>
          <button 
            className={activeTab === 'drift' ? 'active' : ''}
            onClick={() => setActiveTab('drift')}
          >
            📈 Drift Detection
          </button>
          <button 
            className={activeTab === 'performance' ? 'active' : ''}
            onClick={() => setActiveTab('performance')}
          >
            🎯 Performance Tracking
          </button>
          <button 
            className={activeTab === 'explainability' ? 'active' : ''}
            onClick={() => setActiveTab('explainability')}
          >
            🔍 Explainability
          </button>
          <button 
            className={activeTab === 'fairness' ? 'active' : ''}
            onClick={() => setActiveTab('fairness')}
          >
            ⚖️ Fairness Monitoring
          </button>
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'metrics' && <MetricsCollectorPanel />}
        {activeTab === 'drift' && <DriftDetectionPanel />}
        {activeTab === 'performance' && <PerformancePanel />}
        {activeTab === 'explainability' && <ExplainabilityPanel />}
        {activeTab === 'fairness' && <FairnessPanel />}
      </main>
    </div>
  );
}

export default App;
EOF

cat > frontend/src/App.css << 'EOF'
.App {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.app-header h1 {
  font-size: 1.8rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(76, 175, 80, 0.1);
  border-radius: 20px;
  font-weight: 600;
  color: #2e7d32;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-indicator.healthy {
  background: #4caf50;
}

.status-indicator.degraded {
  background: #ff9800;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.nav-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 0 2rem 1rem;
  overflow-x: auto;
}

.nav-tabs button {
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  color: #666;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  border-radius: 8px 8px 0 0;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.nav-tabs button:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.nav-tabs button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.app-main {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}
EOF

cat > frontend/src/components/MetricsCollectorPanel.js << 'EOF'
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Panel.css';

function MetricsCollectorPanel() {
  const [stats, setStats] = useState(null);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/metrics/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const sendTestPrediction = async () => {
    try {
      const payload = {
        model_id: 'fraud-detection-v1',
        prediction_id: `pred-${Date.now()}`,
        features: {
          amount: Math.random() * 1000,
          frequency: Math.floor(Math.random() * 20),
          recency: Math.random() * 30
        },
        prediction: Math.random(),
        ground_truth: Math.random() > 0.5 ? 1 : 0
      };

      const response = await axios.post('http://localhost:8000/metrics/collect', payload);
      setTestResult({ success: true, data: response.data });
      loadStats();
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>📊 Metrics Collection Status</h2>
        <button onClick={sendTestPrediction} className="action-button">
          Send Test Prediction
        </button>
      </div>

      {testResult && (
        <div className={`alert ${testResult.success ? 'success' : 'error'}`}>
          {testResult.success ? '✓ Test prediction sent successfully!' : `✗ Error: ${testResult.error}`}
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-label">Total Predictions</div>
            <div className="stat-value">{stats?.total_predictions || 0}</div>
          </div>
        </div>

        {stats?.by_model?.map((model, idx) => (
          <div key={idx} className="stat-card">
            <div className="stat-icon">🎯</div>
            <div className="stat-content">
              <div className="stat-label">{model.model_id}</div>
              <div className="stat-value">{model.count}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="info-section">
        <h3>System Information</h3>
        <p>The metrics collector captures all model predictions in real-time, storing features, predictions, and ground truth labels for downstream analysis.</p>
      </div>
    </div>
  );
}

export default MetricsCollectorPanel;
EOF

cat > frontend/src/components/DriftDetectionPanel.js << 'EOF'
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Panel.css';

function DriftDetectionPanel() {
  const [driftStatus, setDriftStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDriftStatus();
    const interval = setInterval(loadDriftStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDriftStatus = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8001/drift/status');
      setDriftStatus(response.data);
    } catch (error) {
      console.error('Error loading drift status:', error);
    }
    setLoading(false);
  };

  const getChartData = () => {
    if (!driftStatus?.features) return [];
    return Object.entries(driftStatus.features).map(([feature, data]) => ({
      feature,
      'KS Statistic': data.ks_statistic || 0,
      'P-Value': data.p_value || 0
    }));
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>📈 Drift Detection Analysis</h2>
        <button onClick={loadDriftStatus} className="action-button" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh Analysis'}
        </button>
      </div>

      {driftStatus && (
        <>
          <div className="stats-grid">
            {Object.entries(driftStatus.features || {}).map(([feature, data]) => (
              <div key={feature} className={`stat-card ${data.drift_detected ? 'alert' : ''}`}>
                <div className="stat-icon">{data.drift_detected ? '⚠️' : '✓'}</div>
                <div className="stat-content">
                  <div className="stat-label">{feature}</div>
                  <div className="stat-value">
                    {data.drift_detected ? 'Drift Detected' : 'Normal'}
                  </div>
                  <div className="stat-detail">
                    p-value: {data.p_value?.toFixed(4) || 'N/A'}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="chart-container">
            <h3>Feature Drift Scores</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="feature" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip 
                  contentStyle={{ background: '#fff', border: '1px solid #ddd', borderRadius: '8px' }}
                />
                <Legend />
                <Bar dataKey="KS Statistic" fill="#667eea" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

export default DriftDetectionPanel;
EOF

cat > frontend/src/components/PerformancePanel.js << 'EOF'
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Panel.css';

function PerformancePanel() {
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPerformance();
    const interval = setInterval(loadPerformance, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadPerformance = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8002/performance/current');
      setPerformance(response.data);
    } catch (error) {
      console.error('Error loading performance:', error);
    }
    setLoading(false);
  };

  const getMetricsData = () => {
    if (!performance?.metrics) return [];
    return Object.entries(performance.metrics).map(([window, metrics]) => ({
      window,
      Accuracy: (metrics.accuracy * 100).toFixed(2),
      Precision: (metrics.precision * 100).toFixed(2),
      Recall: (metrics.recall * 100).toFixed(2),
      'F1 Score': (metrics.f1 * 100).toFixed(2),
      'AUC-ROC': (metrics.auc_roc * 100).toFixed(2)
    }));
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🎯 Performance Tracking</h2>
        <button onClick={loadPerformance} className="action-button" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh Metrics'}
        </button>
      </div>

      {performance?.metrics && (
        <>
          <div className="stats-grid">
            {Object.entries(performance.metrics).map(([window, metrics]) => (
              <div key={window} className="stat-card large">
                <div className="stat-header">
                  <div className="stat-icon">⏱️</div>
                  <div className="stat-label">{window} Window</div>
                </div>
                <div className="metrics-grid">
                  <div className="metric">
                    <span>Accuracy</span>
                    <strong>{(metrics.accuracy * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>Precision</span>
                    <strong>{(metrics.precision * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>Recall</span>
                    <strong>{(metrics.recall * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>F1 Score</span>
                    <strong>{(metrics.f1 * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>AUC-ROC</span>
                    <strong>{(metrics.auc_roc * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="metric">
                    <span>Samples</span>
                    <strong>{metrics.sample_count}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default PerformancePanel;
EOF

cat > frontend/src/components/ExplainabilityPanel.js << 'EOF'
import React, { useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Panel.css';

function ExplainabilityPanel() {
  const [predictionId, setPredictionId] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateExplanation = async (type) => {
    if (!predictionId.trim()) {
      alert('Please enter a prediction ID');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`http://localhost:8003/explain/${type}`, {
        prediction_id: predictionId,
        model_id: 'default'
      });
      setExplanation(response.data);
    } catch (error) {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    }
    setLoading(false);
  };

  const getChartData = () => {
    if (!explanation?.explanation) return [];
    const values = explanation.explanation.shap_values || explanation.explanation.weights || {};
    return Object.entries(values).map(([feature, value]) => ({
      feature,
      contribution: Math.abs(value),
      positive: value > 0
    }));
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🔍 Model Explainability</h2>
      </div>

      <div className="input-section">
        <input
          type="text"
          placeholder="Enter Prediction ID (e.g., pred-1234567890)"
          value={predictionId}
          onChange={(e) => setPredictionId(e.target.value)}
          className="text-input"
        />
        <div className="button-group">
          <button 
            onClick={() => generateExplanation('shap')} 
            className="action-button"
            disabled={loading}
          >
            Generate SHAP Explanation
          </button>
          <button 
            onClick={() => generateExplanation('lime')} 
            className="action-button secondary"
            disabled={loading}
          >
            Generate LIME Explanation
          </button>
        </div>
      </div>

      {explanation && (
        <div className="explanation-results">
          <div className="result-header">
            <h3>{explanation.explanation_type.toUpperCase()} Explanation</h3>
            <span className="prediction-id">ID: {explanation.prediction_id}</span>
          </div>

          {explanation.explanation.base_value !== undefined && (
            <div className="base-value">
              <span>Base Value:</span>
              <strong>{explanation.explanation.base_value.toFixed(4)}</strong>
            </div>
          )}

          {explanation.explanation.predicted_value !== undefined && (
            <div className="predicted-value">
              <span>Predicted Value:</span>
              <strong>{explanation.explanation.predicted_value.toFixed(4)}</strong>
            </div>
          )}

          <div className="chart-container">
            <h4>Feature Contributions</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="feature" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip 
                  contentStyle={{ background: '#fff', border: '1px solid #ddd', borderRadius: '8px' }}
                />
                <Bar dataKey="contribution" fill="#667eea" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExplainabilityPanel;
EOF

cat > frontend/src/components/FairnessPanel.js << 'EOF'
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Panel.css';

function FairnessPanel() {
  const [fairness, setFairness] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadFairness();
    loadAlerts();
    const interval = setInterval(() => {
      loadFairness();
      loadAlerts();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadFairness = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8004/fairness/current');
      setFairness(response.data);
    } catch (error) {
      console.error('Error loading fairness:', error);
    }
    setLoading(false);
  };

  const loadAlerts = async () => {
    try {
      const response = await axios.get('http://localhost:8004/fairness/alerts');
      setAlerts(response.data);
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>⚖️ Fairness Monitoring</h2>
        <button onClick={() => { loadFairness(); loadAlerts(); }} className="action-button" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh Analysis'}
        </button>
      </div>

      {alerts.length > 0 && (
        <div className="alert error">
          ⚠️ {alerts.length} fairness alert(s) detected in the last 24 hours
        </div>
      )}

      {fairness?.metrics && (
        <div className="fairness-metrics">
          {Object.entries(fairness.metrics).map(([key, data]) => (
            <div key={key} className="fairness-card">
              <h3>{key.replace(/_/g, ' ').toUpperCase()}</h3>
              
              {data.disparity !== undefined && (
                <div className="disparity-indicator">
                  <span>Disparity:</span>
                  <strong className={data.disparity > 0.1 ? 'high' : 'normal'}>
                    {(data.disparity * 100).toFixed(2)}%
                  </strong>
                </div>
              )}

              {data.groups && (
                <div className="groups-breakdown">
                  <h4>Groups:</h4>
                  {Object.entries(data.groups).map(([group, value]) => (
                    <div key={group} className="group-metric">
                      <span>{group}:</span>
                      <span>
                        {typeof value === 'object' 
                          ? `TPR: ${(value.tpr * 100).toFixed(1)}%, FPR: ${(value.fpr * 100).toFixed(1)}%`
                          : `${(value * 100).toFixed(1)}%`
                        }
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="info-section">
        <h3>Fairness Metrics</h3>
        <p><strong>Demographic Parity:</strong> Measures equal approval rates across groups</p>
        <p><strong>Equalized Odds:</strong> Ensures equal TPR and FPR across groups</p>
        <p><strong>Threshold:</strong> Alerts trigger when disparity exceeds 10%</p>
      </div>
    </div>
  );
}

export default FairnessPanel;
EOF

cat > frontend/src/components/Panel.css << 'EOF'
.panel {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  animation: slideIn 0.4s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.panel-header h2 {
  font-size: 1.8rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.action-button {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.action-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-button.secondary {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
}

.alert {
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  animation: slideIn 0.3s ease;
}

.alert.success {
  background: #e8f5e9;
  color: #2e7d32;
  border-left: 4px solid #4caf50;
}

.alert.error {
  background: #ffebee;
  color: #c62828;
  border-left: 4px solid #f44336;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  padding: 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-card.alert {
  background: linear-gradient(135deg, #fff3e0 0%, #ffffff 100%);
  border-left: 4px solid #ff9800;
}

.stat-card.large {
  grid-column: span 2;
  flex-direction: column;
  align-items: stretch;
}

.stat-icon {
  font-size: 2rem;
}

.stat-content {
  flex: 1;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-detail {
  font-size: 0.85rem;
  color: #999;
  margin-top: 0.25rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metric span {
  font-size: 0.85rem;
  color: #666;
}

.metric strong {
  font-size: 1.2rem;
  color: #667eea;
}

.chart-container {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  margin-top: 1.5rem;
}

.chart-container h3, .chart-container h4 {
  margin-bottom: 1rem;
  color: #333;
}

.info-section {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  margin-top: 1.5rem;
}

.info-section h3 {
  margin-bottom: 0.75rem;
  color: #333;
}

.info-section p {
  color: #666;
  line-height: 1.6;
  margin-bottom: 0.5rem;
}

.input-section {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.text-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
  margin-bottom: 1rem;
}

.text-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.button-group {
  display: flex;
  gap: 1rem;
}

.button-group button {
  flex: 1;
}

.explanation-results {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  margin-top: 1.5rem;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.result-header h3 {
  color: #667eea;
}

.prediction-id {
  font-size: 0.9rem;
  color: #666;
  background: white;
  padding: 0.5rem 1rem;
  border-radius: 6px;
}

.base-value, .predicted-value {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.base-value span, .predicted-value span {
  color: #666;
}

.base-value strong, .predicted-value strong {
  color: #667eea;
  font-size: 1.1rem;
}

.fairness-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.fairness-card {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
}

.fairness-card h3 {
  color: #667eea;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.disparity-indicator {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.disparity-indicator strong {
  font-size: 1.2rem;
}

.disparity-indicator strong.high {
  color: #f44336;
}

.disparity-indicator strong.normal {
  color: #4caf50;
}

.groups-breakdown h4 {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.group-metric {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e0e0e0;
}

.group-metric:last-child {
  border-bottom: none;
}

.group-metric span:first-child {
  color: #666;
  font-weight: 600;
}

.group-metric span:last-child {
  color: #333;
}
EOF

# Create database initialization script
echo "Creating database setup..."
cat > backend/init_db.py << 'EOF'
import asyncio
import asyncpg

async def init_database():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='postgres'
    )
    
    # Create database
    try:
        await conn.execute('CREATE DATABASE monitoring')
        print("✓ Database created")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("✓ Database already exists")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(init_database())
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
asyncpg==0.29.0
numpy==1.26.3
scipy==1.12.0
scikit-learn==1.4.0
pydantic==2.5.3
prometheus-client==0.19.0
python-multipart==0.0.6
aiofiles==23.2.1
EOF

# Create Docker Compose
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: monitoring
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  metrics-collector:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python backend/metrics_collector/collector.py
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/monitoring

  drift-detector:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python backend/drift_detector/detector.py
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/monitoring

  performance-tracker:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python backend/performance_tracker/tracker.py
    ports:
      - "8002:8002"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/monitoring

  explainability:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python backend/explainability/service.py
    ports:
      - "8003:8003"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/monitoring

  fairness-monitor:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python backend/fairness_monitor/monitor.py
    ports:
      - "8004:8004"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/monitoring

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - metrics-collector
      - drift-detector
      - performance-tracker
      - explainability
      - fairness-monitor

volumes:
  postgres_data:
EOF

# Create Dockerfiles
mkdir -p docker

cat > docker/Dockerfile.backend << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY data/ data/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.metrics_collector.collector:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

cat > docker/Dockerfile.frontend << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY public/ public/
COPY src/ src/

EXPOSE 3000

CMD ["npm", "start"]
EOF

# Create .dockerignore
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
node_modules/
EOF

# Create test suite
echo "Creating test suite..."
cat > tests/test_monitoring.py << 'EOF'
import pytest
import asyncio
import asyncpg
from datetime import datetime
import sys
sys.path.append('backend')

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='monitoring'
    )
    assert conn is not None
    await conn.close()
    print("✓ Database connection test passed")

@pytest.mark.asyncio
async def test_prediction_storage():
    """Test prediction storage"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='monitoring'
    )
    
    # Store test prediction
    await conn.execute('''
        INSERT INTO predictions 
        (timestamp, model_id, prediction_id, features, prediction, ground_truth)
        VALUES ($1, $2, $3, $4, $5, $6)
    ''', datetime.utcnow(), 'test-model', 'test-pred-1',
        '{"amount": 100.0, "frequency": 5}', 0.75, 1)
    
    # Verify storage
    result = await conn.fetchval(
        'SELECT COUNT(*) FROM predictions WHERE model_id = $1',
        'test-model'
    )
    
    assert result > 0
    await conn.close()
    print("✓ Prediction storage test passed")

if __name__ == "__main__":
    asyncio.run(test_database_connection())
    asyncio.run(test_prediction_storage())
    print("\n✓ All tests passed!")
EOF

# Create data generator for testing
cat > backend/generate_test_data.py << 'EOF'
import asyncio
import asyncpg
import numpy as np
from datetime import datetime, timedelta
import json

async def generate_test_data(num_samples=1000):
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='monitoring'
    )
    
    print(f"Generating {num_samples} test predictions...")
    
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(num_samples):
        timestamp = base_time + timedelta(seconds=i * 86)
        
        features = {
            'amount': float(np.random.normal(100, 30)),
            'frequency': float(np.random.normal(5, 2)),
            'recency': float(np.random.exponential(10))
        }
        
        # Simulate prediction with some correlation to features
        prediction = 1 / (1 + np.exp(-(features['amount'] / 100 + features['frequency'] / 5) + np.random.normal(0, 0.5)))
        ground_truth = 1 if prediction > 0.5 else 0
        
        await conn.execute('''
            INSERT INTO predictions 
            (timestamp, model_id, prediction_id, features, prediction, ground_truth)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''', timestamp, 'default', f'pred-{i}',
            json.dumps(features), float(prediction), ground_truth)
    
    print(f"✓ Generated {num_samples} test predictions")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(generate_test_data())
EOF

# Create start script
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Model Monitoring Platform..."

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start PostgreSQL (if not using Docker)
if ! docker ps | grep -q postgres; then
    echo "Starting PostgreSQL..."
    docker run -d --name monitoring-postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=monitoring \
        -p 5432:5432 \
        postgres:15-alpine
    sleep 5
fi

# Initialize database
echo "Initializing database..."
python backend/init_db.py

# Generate test data
echo "Generating test data..."
python backend/generate_test_data.py

# Start backend services
echo "Starting backend services..."
python backend/metrics_collector/collector.py &
python backend/drift_detector/detector.py &
python backend/performance_tracker/tracker.py &
python backend/explainability/service.py &
python backend/fairness_monitor/monitor.py &

# Start frontend
cd frontend
npm install
npm start &

echo "✅ Platform started!"
echo ""
echo "Access points:"
echo "  - Dashboard: http://localhost:3000"
echo "  - Metrics Collector: http://localhost:8000"
echo "  - Drift Detector: http://localhost:8001"
echo "  - Performance Tracker: http://localhost:8002"
echo "  - Explainability Service: http://localhost:8003"
echo "  - Fairness Monitor: http://localhost:8004"
EOF

chmod +x start.sh

# Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash

echo "Stopping Model Monitoring Platform..."

# Kill Python processes
pkill -f "python backend"
pkill -f "npm start"

# Stop Docker containers
docker stop monitoring-postgres 2>/dev/null
docker rm monitoring-postgres 2>/dev/null

echo "✅ Platform stopped"
EOF

chmod +x stop.sh

echo ""
echo "✅ Project structure created successfully!"
echo ""
echo "Created files:"
find . -type f -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.yml" | sort

echo ""
echo "To start the platform:"
echo "  ./start.sh"
echo ""
echo "To stop the platform:"
echo "  ./stop.sh"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up --build"