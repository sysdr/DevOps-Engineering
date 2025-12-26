from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            port=5433,
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
