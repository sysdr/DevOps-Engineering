from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
import asyncpg
import asyncio
from datetime import datetime
import json
import logging

from services.cost_collector import CostCollector
from services.spot_manager import SpotInstanceManager
from services.inference_optimizer import InferenceOptimizer
from services.job_scheduler import JobScheduler
from services.analytics import CostAnalytics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MLOps Cost Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
db_pool = None
cost_collector = None
spot_manager = None
inference_optimizer = None
job_scheduler = None
analytics = None
websocket_clients = []

@app.on_event("startup")
async def startup():
    global db_pool, cost_collector, spot_manager, inference_optimizer, job_scheduler, analytics
    
    # Initialize database
    db_pool = await asyncpg.create_pool(
        host="localhost",
        port=5433,
        user="postgres",
        password="postgres",
        database="mlops_costs"
    )
    
    # Create tables
    async with db_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS cost_records (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                team VARCHAR(100),
                project VARCHAR(100),
                instance_type VARCHAR(50),
                runtime_hours FLOAT,
                cost FLOAT
            )
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_cost_timestamp ON cost_records(timestamp)
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_cost_team ON cost_records(team)
        ''')
    
    # Initialize services
    cost_collector = CostCollector(db_pool)
    spot_manager = SpotInstanceManager(db_pool)
    inference_optimizer = InferenceOptimizer()
    job_scheduler = JobScheduler(db_pool, spot_manager)
    analytics = CostAnalytics(db_pool)
    
    # Initialize spot pool
    await spot_manager.initialize_spot_pool("g4dn.2xlarge", 5)
    
    # Start background tasks
    asyncio.create_task(cost_collector.run_collection_loop())
    asyncio.create_task(broadcast_metrics())
    
    logger.info("MLOps Cost Optimizer started")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

async def broadcast_metrics():
    """Broadcast real-time metrics to connected clients"""
    while True:
        if websocket_clients:
            try:
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cost_summary": await analytics.get_cost_summary(days=1),
                    "spot_stats": await spot_manager.get_spot_statistics(),
                    "queue_stats": await job_scheduler.get_queue_stats()
                }
                
                message = json.dumps(metrics)
                for client in websocket_clients:
                    try:
                        await client.send_text(message)
                    except:
                        websocket_clients.remove(client)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
        
        await asyncio.sleep(5)

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)

@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests to prevent 404 errors"""
    return Response(status_code=204)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/costs")
async def get_costs(days: int = 7):
    """Get cost summary"""
    return await analytics.get_cost_summary(days=days)

@app.get("/api/costs/forecast/{team}")
async def get_forecast(team: str):
    """Get spending forecast for team"""
    return await analytics.get_team_forecast(team)

@app.post("/api/jobs/submit")
async def submit_job(job: dict):
    """Submit ML job for scheduling"""
    result = await job_scheduler.submit_job(job)
    return result

@app.get("/api/jobs/queue")
async def get_queue():
    """Get job queue status"""
    return await job_scheduler.get_queue_stats()

@app.post("/api/optimize/inference")
async def optimize_inference(model_id: str, latency_sla: float = 100.0):
    """Optimize model inference deployment"""
    optimal = await inference_optimizer.optimize_model(model_id, latency_sla)
    return optimal

@app.get("/api/spot/stats")
async def get_spot_stats():
    """Get spot instance statistics"""
    return await spot_manager.get_spot_statistics()

@app.get("/api/spot/instances")
async def get_spot_instances():
    """Get list of all spot instances"""
    instances = await spot_manager.get_spot_instances()
    return {"instances": instances}

@app.post("/api/spot/interrupt/{instance_id}")
async def simulate_interrupt(instance_id: str):
    """Simulate spot instance interruption"""
    result = await spot_manager.simulate_spot_interruption(instance_id)
    return result

@app.post("/api/analytics/roi")
async def calculate_roi(model_id: str, revenue_impact: float):
    """Calculate model ROI"""
    return await analytics.calculate_roi(model_id, revenue_impact)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
