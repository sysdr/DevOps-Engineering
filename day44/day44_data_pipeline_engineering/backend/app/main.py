from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))

app = FastAPI(title="Data Pipeline Monitor", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections: List[WebSocket] = []

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Get overall pipeline status"""
    try:
        # Load ingestion metrics
        metrics_path = Path('/tmp/pipeline_data/metrics/ingestion_metrics.json')
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                ingestion_metrics = json.load(f)
        else:
            ingestion_metrics = {}
        
        # Load validation results
        validation_path = Path('/tmp/pipeline_data/validation/results.json')
        if validation_path.exists():
            with open(validation_path, 'r') as f:
                validation_results = json.load(f)
        else:
            validation_results = {}
        
        # Get DVC versions
        dvc_versions_path = Path('/tmp/dvc_storage/versions.json')
        if dvc_versions_path.exists():
            with open(dvc_versions_path, 'r') as f:
                versions = json.load(f)
                latest_version = versions[-1] if versions else None
        else:
            latest_version = None
        
        status = {
            'pipeline_health': 'healthy',
            'ingestion': {
                'status': 'running' if ingestion_metrics else 'idle',
                'total_records': ingestion_metrics.get('total_records', 0),
                'total_users': ingestion_metrics.get('total_users', 0),
                'total_purchases': ingestion_metrics.get('total_purchases', 0),
                'avg_amount': ingestion_metrics.get('avg_amount', 0),
                'last_run': ingestion_metrics.get('processed_at', 'N/A')
            },
            'validation': {
                'score': validation_results.get('validation_score', 0),
                'passed_checks': validation_results.get('passed_checks', 0),
                'total_checks': validation_results.get('total_checks', 0),
                'failures': validation_results.get('failures', []),
                'last_run': validation_results.get('timestamp', 'N/A')
            },
            'versioning': {
                'latest_version': latest_version['version'] if latest_version else 'N/A',
                'total_versions': len(versions) if dvc_versions_path.exists() else 0
            },
            'streaming': {
                'kafka_topics': ['raw-events', 'validated-events', 'aggregated-events'],
                'status': 'active'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/validation/history")
async def get_validation_history():
    """Get validation history"""
    validation_path = Path('/tmp/pipeline_data/validation/results.json')
    if validation_path.exists():
        with open(validation_path, 'r') as f:
            return json.load(f)
    return {}

@app.get("/api/versions")
async def get_versions():
    """Get DVC version history"""
    versions_path = Path('/tmp/dvc_storage/versions.json')
    if versions_path.exists():
        with open(versions_path, 'r') as f:
            return json.load(f)
    return []

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send pipeline metrics every 2 seconds
            status = await get_pipeline_status()
            await websocket.send_json(status)
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
