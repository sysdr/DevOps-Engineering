from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os
# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from models.forecaster import TimeSeriesForecaster, AnomalyDetector
from agents.scaling_agent import PredictiveScalingAgent, IncidentResponseAgent

app = FastAPI(title="AI Infrastructure Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global objects
db_pool = None
forecaster = None
anomaly_detector = None
scaling_agent = None
incident_agent = None

@app.on_event("startup")
async def startup():
    global db_pool, forecaster, anomaly_detector, scaling_agent, incident_agent
    
    db_pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres',
        database='postgres',
        min_size=5,
        max_size=20
    )
    
    forecaster = TimeSeriesForecaster(db_pool)
    anomaly_detector = AnomalyDetector()
    scaling_agent = PredictiveScalingAgent(db_pool, forecaster)
    incident_agent = IncidentResponseAgent(db_pool)
    
    # Train initial models
    asyncio.create_task(train_models_periodic())
    asyncio.create_task(monitor_anomalies())
    asyncio.create_task(run_scaling_decisions())
    
    print("✅ AI Infrastructure API started")

async def train_models_periodic():
    """Train models periodically"""
    await asyncio.sleep(30)  # Wait for initial data
    
    metrics = ['cpu_usage_percent', 'memory_usage_percent', 'network_bytes_sent']
    
    while True:
        try:
            for metric in metrics:
                await forecaster.train_model(metric)
            print("✅ Models retrained")
        except Exception as e:
            print(f"Error training models: {e}")
        
        await asyncio.sleep(3600)  # Every hour

async def monitor_anomalies():
    """Monitor metrics for anomalies"""
    await asyncio.sleep(60)  # Wait for data
    
    while True:
        try:
            # Check recent metrics
            recent_time = datetime.now() - timedelta(seconds=30)
            
            rows = await db_pool.fetch('''
                SELECT DISTINCT ON (metric_name, node_name)
                    metric_name, node_name, value, time
                FROM metrics
                WHERE time >= $1
                ORDER BY metric_name, node_name, time DESC
            ''', recent_time)
            
            for row in rows:
                # Get historical values
                historical = await db_pool.fetch('''
                    SELECT value FROM metrics
                    WHERE metric_name = $1 AND node_name = $2
                    AND time >= $3
                    ORDER BY time ASC
                ''', row['metric_name'], row['node_name'], 
                     datetime.now() - timedelta(minutes=30))
                
                recent_values = [float(r['value']) for r in historical[:-1]]
                current_value = float(row['value'])
                
                if len(recent_values) >= 50:
                    result = await anomaly_detector.detect(
                        row['metric_name'], current_value, recent_values, db_pool
                    )
                    
                    if result['is_anomaly']:
                        # Trigger incident response
                        anomaly_id = await db_pool.fetchval('''
                            SELECT id FROM anomalies ORDER BY id DESC LIMIT 1
                        ''')
                        await incident_agent.analyze_root_cause(anomaly_id)
            
        except Exception as e:
            print(f"Error monitoring anomalies: {e}")
        
        await asyncio.sleep(30)

async def run_scaling_decisions():
    """Run scaling agent periodically"""
    await asyncio.sleep(120)  # Wait for models to train
    
    deployments = ['nginx', 'api-service', 'worker-pool']
    
    while True:
        try:
            for deployment in deployments:
                await scaling_agent.make_scaling_decision(deployment)
        except Exception as e:
            print(f"Error in scaling decisions: {e}")
        
        await asyncio.sleep(300)  # Every 5 minutes

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/metrics/current")
async def get_current_metrics():
    """Get latest metrics for all nodes"""
    rows = await db_pool.fetch('''
        SELECT DISTINCT ON (node_name, metric_name)
            node_name, metric_name, value, time
        FROM metrics
        ORDER BY node_name, metric_name, time DESC
    ''')
    
    result = {}
    for row in rows:
        node = row['node_name']
        if node not in result:
            result[node] = {}
        result[node][row['metric_name']] = {
            'value': float(row['value']),
            'timestamp': row['time'].isoformat()
        }
    
    return result

@app.get("/api/metrics/history/{metric_name}")
async def get_metric_history(metric_name: str, hours: int = 1):
    """Get metric history"""
    start_time = datetime.now() - timedelta(hours=hours)
    
    rows = await db_pool.fetch('''
        SELECT time, node_name, value
        FROM metrics
        WHERE metric_name = $1 AND time >= $2
        ORDER BY time ASC
    ''', metric_name, start_time)
    
    return [{
        'timestamp': row['time'].isoformat(),
        'node': row['node_name'],
        'value': float(row['value'])
    } for row in rows]

@app.post("/api/models/train")
async def trigger_training():
    """Manually trigger model training"""
    metrics = ['cpu_usage_percent', 'memory_usage_percent', 'network_bytes_sent']
    
    for metric in metrics:
        await forecaster.train_model(metric)
    
    return {"status": "training_complete", "metrics": metrics}

@app.get("/api/predictions/{metric_name}")
async def get_predictions(metric_name: str):
    """Get predictions for a metric"""
    try:
        # Get recent values
        recent = await db_pool.fetch('''
            SELECT value FROM metrics
            WHERE metric_name = $1
            ORDER BY time DESC
            LIMIT 60
        ''', metric_name)
        
        if len(recent) < 60:
            return {
                'metric': metric_name,
                'predicted_value': None,
                'confidence_lower': None,
                'confidence_upper': None,
                'horizon_minutes': 15,
                'timestamp': datetime.now().isoformat(),
                'status': 'insufficient_data',
                'message': f'Insufficient data: {len(recent)}/60 data points required'
            }
        
        recent_values = [float(r['value']) for r in reversed(recent)]
        
        try:
            predicted, conf_lower, conf_upper = await forecaster.predict(metric_name, recent_values)
        except Exception as e:
            print(f"Error in prediction: {e}")
            return {
                'metric': metric_name,
                'predicted_value': None,
                'confidence_lower': None,
                'confidence_upper': None,
                'horizon_minutes': 15,
                'timestamp': datetime.now().isoformat(),
                'status': 'prediction_error',
                'message': f'Prediction error: {str(e)}'
            }
        
        if predicted is None:
            return {
                'metric': metric_name,
                'predicted_value': None,
                'confidence_lower': None,
                'confidence_upper': None,
                'horizon_minutes': 15,
                'timestamp': datetime.now().isoformat(),
                'status': 'model_not_trained',
                'message': 'Model not trained yet'
            }
        
        return {
            'metric': metric_name,
            'predicted_value': predicted,
            'confidence_lower': conf_lower,
            'confidence_upper': conf_upper,
            'horizon_minutes': 15,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    except Exception as e:
        print(f"Error in get_predictions: {e}")
        return {
            'metric': metric_name,
            'predicted_value': None,
            'confidence_lower': None,
            'confidence_upper': None,
            'horizon_minutes': 15,
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'message': f'Error: {str(e)}'
        }

@app.get("/api/anomalies/recent")
async def get_recent_anomalies(hours: int = 24):
    """Get recent anomalies"""
    start_time = datetime.now() - timedelta(hours=hours)
    
    rows = await db_pool.fetch('''
        SELECT * FROM anomalies
        WHERE detected_at >= $1
        ORDER BY detected_at DESC
    ''', start_time)
    
    return [{
        'id': row['id'],
        'detected_at': row['detected_at'].isoformat(),
        'metric_name': row['metric_name'],
        'value': float(row['value']),
        'expected_value': float(row['expected_value']),
        'severity': row['severity'],
        'detector_votes': row['detector_votes']
    } for row in rows]

@app.get("/api/incidents/recent")
async def get_recent_incidents(hours: int = 24):
    """Get recent incidents"""
    start_time = datetime.now() - timedelta(hours=hours)
    
    rows = await db_pool.fetch('''
        SELECT * FROM incidents
        WHERE created_at >= $1
        ORDER BY created_at DESC
    ''', start_time)
    
    return [{
        'id': row['id'],
        'created_at': row['created_at'].isoformat(),
        'title': row['title'],
        'symptoms': row['symptoms'],
        'root_cause': row['root_cause'],
        'remediation_actions': row['remediation_actions'],
        'status': row['status']
    } for row in rows]

@app.get("/api/scaling/decisions")
async def get_scaling_decisions(hours: int = 24):
    """Get recent scaling decisions"""
    start_time = datetime.now() - timedelta(hours=hours)
    
    rows = await db_pool.fetch('''
        SELECT * FROM scaling_decisions
        WHERE timestamp >= $1
        ORDER BY timestamp DESC
    ''', start_time)
    
    return [{
        'id': row['id'],
        'timestamp': row['timestamp'].isoformat(),
        'deployment': row['deployment'],
        'current_replicas': row['current_replicas'],
        'target_replicas': row['target_replicas'],
        'reason': row['reason'],
        'predicted_load': float(row['predicted_load']),
        'executed': row['executed']
    } for row in rows]

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get overall statistics for dashboard"""
    # Model performance
    model_perf = await db_pool.fetchrow('''
        SELECT AVG(accuracy) as avg_accuracy
        FROM model_performance
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
    ''')
    
    # Anomaly count
    anomaly_count = await db_pool.fetchval('''
        SELECT COUNT(*) FROM anomalies
        WHERE detected_at >= NOW() - INTERVAL '24 hours'
    ''')
    
    # Active incidents
    active_incidents = await db_pool.fetchval('''
        SELECT COUNT(*) FROM incidents
        WHERE status != 'resolved'
    ''')
    
    # Scaling actions
    scaling_actions = await db_pool.fetchval('''
        SELECT COUNT(*) FROM scaling_decisions
        WHERE timestamp >= NOW() - INTERVAL '24 hours' AND executed = true
    ''')
    
    return {
        'model_accuracy': float(model_perf['avg_accuracy'] or 0),
        'anomalies_24h': anomaly_count,
        'active_incidents': active_incidents,
        'scaling_actions_24h': scaling_actions,
        'cluster_health': 'optimal' if active_incidents == 0 else 'degraded'
    }

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket for real-time metrics"""
    await websocket.accept()
    
    try:
        while True:
            # Send current metrics
            metrics = await get_current_metrics()
            await websocket.send_json({
                'type': 'metrics_update',
                'data': metrics,
                'timestamp': datetime.now().isoformat()
            })
            
            await asyncio.sleep(5)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
