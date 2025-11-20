"""
Day 30: Prometheus Metrics Application
Production-grade metrics instrumentation with custom business metrics
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Summary,
    generate_latest, CONTENT_TYPE_LATEST, REGISTRY,
    CollectorRegistry
)

# =============================================================================
# CUSTOM METRICS DEFINITION
# =============================================================================

# Request metrics (RED method)
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Business metrics
orders_created_total = Counter(
    'orders_created_total',
    'Total orders created',
    ['payment_method', 'region', 'status']
)

order_value_dollars = Histogram(
    'order_value_dollars',
    'Order value distribution in dollars',
    ['region'],
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
)

inventory_level = Gauge(
    'inventory_items_available',
    'Current inventory level by product',
    ['product_id', 'warehouse']
)

active_users = Gauge(
    'active_users_total',
    'Number of currently active users'
)

# System metrics
app_info = Info(
    'app',
    'Application information'
)

database_connections = Gauge(
    'database_connections_total',
    'Number of database connections',
    ['state']
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Cache operations',
    ['operation', 'result']
)

queue_depth = Gauge(
    'queue_depth_messages',
    'Number of messages in queue',
    ['queue_name']
)

# SLO tracking
slo_requests_total = Counter(
    'slo_requests_total',
    'Total requests for SLO tracking',
    ['slo_class']
)

# Alert tracking (for webhook)
alerts_received = []
max_alerts_stored = 100

# =============================================================================
# APPLICATION SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for background tasks"""
    # Set application info
    app_info.info({
        'version': '1.0.0',
        'environment': 'production',
        'python_version': '3.11'
    })
    
    # Initialize inventory
    for product_id in ['SKU001', 'SKU002', 'SKU003']:
        for warehouse in ['us-east', 'us-west', 'eu-central']:
            inventory_level.labels(
                product_id=product_id,
                warehouse=warehouse
            ).set(random.randint(50, 500))
    
    # Initialize database connections
    database_connections.labels(state='active').set(5)
    database_connections.labels(state='idle').set(15)
    
    # Start background metrics simulation
    task = asyncio.create_task(simulate_metrics())
    
    yield
    
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Prometheus Metrics Demo",
    description="Day 30: Advanced Prometheus Metrics Implementation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# MIDDLEWARE FOR AUTOMATIC METRICS
# =============================================================================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Automatically collect metrics for all requests"""
    method = request.method
    endpoint = request.url.path
    
    # Skip metrics endpoint itself
    if endpoint == "/metrics":
        return await call_next(request)
    
    # Track in-progress requests
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status = str(response.status_code)
    except Exception as e:
        status = "500"
        raise
    finally:
        # Record duration
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Record request count
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        # Track SLO
        if duration < 0.2:
            slo_requests_total.labels(slo_class='fast').inc()
        elif duration < 1.0:
            slo_requests_total.labels(slo_class='acceptable').inc()
        else:
            slo_requests_total.labels(slo_class='slow').inc()
        
        # Decrease in-progress
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
    
    return response

# =============================================================================
# BACKGROUND METRICS SIMULATION
# =============================================================================

async def simulate_metrics():
    """Simulate realistic metric changes"""
    while True:
        try:
            # Fluctuate active users
            current_users = random.randint(100, 1000)
            active_users.set(current_users)
            
            # Update queue depths
            for queue in ['orders', 'notifications', 'analytics']:
                queue_depth.labels(queue_name=queue).set(
                    random.randint(0, 100)
                )
            
            # Simulate inventory changes
            for product_id in ['SKU001', 'SKU002', 'SKU003']:
                for warehouse in ['us-east', 'us-west', 'eu-central']:
                    current = inventory_level.labels(
                        product_id=product_id,
                        warehouse=warehouse
                    )._value.get()
                    change = random.randint(-5, 10)
                    new_value = max(0, current + change)
                    inventory_level.labels(
                        product_id=product_id,
                        warehouse=warehouse
                    ).set(new_value)
            
            # Simulate cache operations
            cache_operations_total.labels(
                operation='get',
                result='hit' if random.random() > 0.2 else 'miss'
            ).inc()
            
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Simulation error: {e}")
            await asyncio.sleep(5)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "prometheus-metrics-demo",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

@app.post("/orders")
async def create_order(
    value: float = 100.0,
    payment_method: str = "credit_card",
    region: str = "us-east"
):
    """Create an order and record metrics"""
    # Simulate processing time
    delay = random.uniform(0.01, 0.3)
    await asyncio.sleep(delay)
    
    # Simulate occasional failures
    if random.random() < 0.05:
        orders_created_total.labels(
            payment_method=payment_method,
            region=region,
            status='failed'
        ).inc()
        raise HTTPException(status_code=500, detail="Order processing failed")
    
    # Record successful order
    orders_created_total.labels(
        payment_method=payment_method,
        region=region,
        status='success'
    ).inc()
    
    order_value_dollars.labels(region=region).observe(value)
    
    # Update inventory
    product_id = random.choice(['SKU001', 'SKU002', 'SKU003'])
    inventory_level.labels(
        product_id=product_id,
        warehouse=region
    ).dec()
    
    return {
        "order_id": f"ORD-{random.randint(10000, 99999)}",
        "value": value,
        "payment_method": payment_method,
        "region": region,
        "status": "created"
    }

@app.get("/orders/simulate")
async def simulate_orders(count: int = 10):
    """Generate simulated orders for testing"""
    results = []
    payment_methods = ['credit_card', 'debit_card', 'paypal', 'crypto']
    regions = ['us-east', 'us-west', 'eu-central', 'ap-south']
    
    for _ in range(count):
        value = random.uniform(10, 1000)
        payment = random.choice(payment_methods)
        region = random.choice(regions)
        
        try:
            result = await create_order(value, payment, region)
            results.append(result)
        except HTTPException:
            results.append({"status": "failed"})
    
    return {
        "simulated": count,
        "successful": len([r for r in results if r.get("status") != "failed"]),
        "failed": len([r for r in results if r.get("status") == "failed"])
    }

@app.get("/slow")
async def slow_endpoint():
    """Deliberately slow endpoint for testing latency alerts"""
    delay = random.uniform(0.5, 2.0)
    await asyncio.sleep(delay)
    return {"message": "slow response", "delay": delay}

@app.get("/error")
async def error_endpoint():
    """Endpoint that sometimes fails for testing error alerts"""
    if random.random() < 0.7:
        raise HTTPException(status_code=500, detail="Simulated error")
    return {"message": "success"}

@app.post("/webhook/alerts")
async def receive_alerts(request: Request):
    """Receive alerts from Alertmanager"""
    global alerts_received
    
    try:
        alert_data = await request.json()
        
        alert_entry = {
            "received_at": datetime.utcnow().isoformat(),
            "data": alert_data
        }
        
        alerts_received.insert(0, alert_entry)
        
        # Keep only recent alerts
        if len(alerts_received) > max_alerts_stored:
            alerts_received = alerts_received[:max_alerts_stored]
        
        print(f"Alert received: {alert_data.get('status', 'unknown')} - "
              f"{len(alert_data.get('alerts', []))} alert(s)")
        
        return {"status": "received", "alert_count": len(alert_data.get('alerts', []))}
    except Exception as e:
        print(f"Error processing alert: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/alerts")
async def get_alerts():
    """Get received alerts"""
    return {
        "total": len(alerts_received),
        "alerts": alerts_received[:20]
    }

@app.get("/dashboard/data")
async def dashboard_data():
    """Get aggregated data for dashboard"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "active_users": active_users._value.get(),
            "queues": {
                "orders": queue_depth.labels(queue_name='orders')._value.get(),
                "notifications": queue_depth.labels(queue_name='notifications')._value.get(),
                "analytics": queue_depth.labels(queue_name='analytics')._value.get()
            },
            "database": {
                "active": database_connections.labels(state='active')._value.get(),
                "idle": database_connections.labels(state='idle')._value.get()
            }
        },
        "recent_alerts": len(alerts_received)
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "checks": {
            "database": "connected",
            "cache": "available",
            "queue": "operational"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
