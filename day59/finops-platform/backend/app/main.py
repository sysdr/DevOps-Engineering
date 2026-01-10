from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from prometheus_client import make_asgi_app, Counter, Gauge, Histogram
import asyncio
import json
from datetime import datetime
from .api import cost_router, optimize_router, alert_router
from .services.cost_collector import CostCollector
from .services.anomaly_detector import AnomalyDetector

app = FastAPI(title="FinOps Platform API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Metrics
cost_total = Gauge('cluster_cost_total', 'Total cluster cost')
cost_by_namespace = Gauge('namespace_cost', 'Cost by namespace', ['namespace'])
optimization_savings = Gauge('optimization_savings', 'Potential savings identified')

# Include routers
app.include_router(cost_router.router, prefix="/api/v1/cost", tags=["cost"])
app.include_router(optimize_router.router, prefix="/api/v1/optimize", tags=["optimize"])
app.include_router(alert_router.router, prefix="/api/v1/alerts", tags=["alerts"])

# Global state
active_connections = []
cost_collector = None
anomaly_detector = None

@app.on_event("startup")
async def startup_event():
    global cost_collector, anomaly_detector
    cost_collector = CostCollector()
    anomaly_detector = AnomalyDetector()
    # Trigger initial collection to populate data immediately
    try:
        await cost_collector.collect_metrics()
        await anomaly_detector.check_anomalies()
    except Exception as e:
        print(f"Error in initial collection: {e}")
    # Start background collection task
    asyncio.create_task(background_collection())

async def background_collection():
    """Background task for continuous cost collection"""
    while True:
        try:
            await cost_collector.collect_metrics()
            await anomaly_detector.check_anomalies()
            await broadcast_updates()
        except Exception as e:
            print(f"Collection error: {e}")
        await asyncio.sleep(300)  # Every 5 minutes

async def broadcast_updates():
    """Send updates to all connected clients"""
    if not active_connections:
        return
    
    if not cost_collector:
        return
    
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_cost": cost_collector.get_total_cost(),
        "namespaces": cost_collector.get_namespace_costs(),
        "anomalies": anomaly_detector.get_recent_anomalies() if anomaly_detector else []
    }
    
    message = json.dumps(data)
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            print(f"Error sending to WebSocket client: {e}")
            disconnected.append(connection)
    
    # Remove disconnected clients
    for connection in disconnected:
        if connection in active_connections:
            active_connections.remove(connection)

@app.websocket("/ws/cost-stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial data when client connects (with proper error handling)
        initial_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_cost": 0,
            "namespaces": {},
            "anomalies": []
        }
        
        try:
            if cost_collector:
                initial_data["total_cost"] = cost_collector.get_total_cost()
                initial_data["namespaces"] = cost_collector.get_namespace_costs()
            if anomaly_detector:
                try:
                    initial_data["anomalies"] = anomaly_detector.get_recent_anomalies()
                except Exception as e:
                    print(f"Error getting anomalies: {e}")
                    initial_data["anomalies"] = []
        except Exception as e:
            print(f"Error getting initial data: {e}")
            import traceback
            traceback.print_exc()
            # Use default empty values
        
        try:
            await websocket.send_text(json.dumps(initial_data))
        except (WebSocketDisconnect, Exception) as e:
            print(f"Error sending initial WebSocket data: {type(e).__name__}: {e}")
            # If we can't send initial data, connection might be closed
            if websocket in active_connections:
                active_connections.remove(websocket)
            return
        
        # Keep connection alive - wait for client messages or disconnect
        # Client doesn't need to send anything - server will broadcast updates via broadcast_updates()
        # If client disconnects, receive_text() will raise WebSocketDisconnect immediately
        while True:
            try:
                # Wait for client message (optional - client can send "ping")
                # If client never sends anything, this will wait indefinitely
                # When client disconnects, this will raise WebSocketDisconnect immediately
                data = await websocket.receive_text()
                # Client sent a message - respond to ping with pong
                if data == "ping":
                    try:
                        await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))
                    except (WebSocketDisconnect, Exception) as e:
                        print(f"Error sending pong: {type(e).__name__}: {e}")
                        break
            except WebSocketDisconnect:
                # Normal client disconnection - exit loop
                break
            except Exception as e:
                # Connection error - log and exit loop
                print(f"WebSocket receive error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                break
    except WebSocketDisconnect:
        # Client disconnected during initial connection or send
        pass
    except Exception as e:
        print(f"WebSocket endpoint error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure connection is removed from active list
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.get("/")
async def root():
    return {"message": "FinOps Platform API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
