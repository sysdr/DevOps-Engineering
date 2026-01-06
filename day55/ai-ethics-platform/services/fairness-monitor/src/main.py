from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ensure shared config is on path
ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT_DIR / "config"))
from database import get_db, FairnessMetric, init_db

app = FastAPI(title="Fairness Monitor Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionLog(BaseModel):
    model_id: str
    prediction: float
    group: str

# In-memory monitoring data
monitoring_data = {}

@app.post("/api/v1/monitor/log")
async def log_prediction(log: PredictionLog, db: Session = Depends(get_db)):
    # Store metric
    metric = FairnessMetric(
        model_id=log.model_id,
        metric_name="approval_rate",
        metric_value=log.prediction,
        group=log.group,
        metadata_json={"timestamp": datetime.utcnow().isoformat()}
    )
    db.add(metric)
    db.commit()
    
    # Update in-memory cache for real-time monitoring
    if log.model_id not in monitoring_data:
        monitoring_data[log.model_id] = {}
    if log.group not in monitoring_data[log.model_id]:
        monitoring_data[log.model_id][log.group] = []
    
    monitoring_data[log.model_id][log.group].append(log.prediction)
    
    # Keep only recent data
    if len(monitoring_data[log.model_id][log.group]) > 1000:
        monitoring_data[log.model_id][log.group] = monitoring_data[log.model_id][log.group][-1000:]
    
    return {"status": "logged"}

@app.get("/api/v1/monitor/metrics/{model_id}")
async def get_current_metrics(model_id: str, db: Session = Depends(get_db)):
    # Get metrics from last 24 hours
    since = datetime.utcnow() - timedelta(hours=24)
    
    metrics = db.query(FairnessMetric).filter(
        FairnessMetric.model_id == model_id,
        FairnessMetric.timestamp >= since
    ).all()
    
    # Aggregate by group
    group_metrics = {}
    for metric in metrics:
        if metric.group not in group_metrics:
            group_metrics[metric.group] = []
        group_metrics[metric.group].append(metric.metric_value)
    
    # Compute summary statistics
    summary = {}
    for group, values in group_metrics.items():
        summary[group] = {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'count': len(values)
        }
    
    # Compute fairness ratio
    if len(summary) >= 2:
        means = [v['mean'] for v in summary.values()]
        fairness_ratio = min(means) / max(means) if max(means) > 0 else 0
    else:
        fairness_ratio = 1.0
    
    return {
        'model_id': model_id,
        'time_window': '24h',
        'group_metrics': summary,
        'fairness_ratio': fairness_ratio,
        'alert_triggered': fairness_ratio < 0.80
    }

@app.get("/api/v1/monitor/trends/{model_id}")
async def get_fairness_trends(model_id: str, days: int = 7, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    
    metrics = db.query(FairnessMetric).filter(
        FairnessMetric.model_id == model_id,
        FairnessMetric.timestamp >= since
    ).order_by(FairnessMetric.timestamp).all()
    
    # Group by day
    daily_metrics = {}
    for metric in metrics:
        day = metric.timestamp.date().isoformat()
        if day not in daily_metrics:
            daily_metrics[day] = {}
        if metric.group not in daily_metrics[day]:
            daily_metrics[day][metric.group] = []
        daily_metrics[day][metric.group].append(metric.metric_value)
    
    # Compute daily fairness ratios
    trend_data = []
    for day, groups in sorted(daily_metrics.items()):
        group_means = {g: np.mean(v) for g, v in groups.items()}
        means = list(group_means.values())
        fairness_ratio = min(means) / max(means) if max(means) > 0 else 0
        
        trend_data.append({
            'date': day,
            'fairness_ratio': fairness_ratio,
            'group_means': group_means
        })
    
    return {
        'model_id': model_id,
        'days': days,
        'trend': trend_data
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "fairness-monitor"}

@app.on_event("startup")
async def startup():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
