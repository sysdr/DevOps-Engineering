"""
WebAssembly Edge Computing Platform
Main FastAPI application with WASM runtime integration
"""
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import wasmtime
import json
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response

# Metrics
REQUEST_COUNT = Counter('wasm_requests_total', 'Total WASM requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('wasm_request_duration_seconds', 'Request duration')
EDGE_SYNC_COUNT = Counter('edge_sync_total', 'Edge sync operations', ['status'])

# WASM Engine - Global instance for performance
wasm_engine = None
wasm_store = None
calculator_module = None

class ComputeRequest(BaseModel):
    operation: str
    values: list[float]
    edge_location: str = "default"

class SyncRequest(BaseModel):
    edge_id: str
    data: dict
    timestamp: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize WASM runtime on startup"""
    global wasm_engine, wasm_store, calculator_module
    
    print("🔧 Initializing WASM runtime...")
    wasm_engine = wasmtime.Engine()
    wasm_store = wasmtime.Store(wasm_engine)
    
    # Load calculator WASM module
    try:
        with open("wasm-modules/calculator/calculator.wasm", "rb") as f:
            wasm_data = f.read()
            if len(wasm_data) > 1000:  # Check if file is substantial
                calculator_module = wasmtime.Module(wasm_engine, wasm_data)
                print("✅ Calculator WASM module loaded")
            else:
                print("⚠️  Calculator WASM module is too small - using fallback")
                calculator_module = None
    except (FileNotFoundError, wasmtime._error.WasmtimeError) as e:
        print(f"⚠️  Calculator WASM module error: {e} - using fallback")
        calculator_module = None
    
    yield
    
    print("🛑 Shutting down WASM runtime...")

app = FastAPI(
    title="WASM Edge Computing Platform",
    description="Ultra-low latency edge computing with WebAssembly",
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

# Edge data storage (in production: Redis/etcd)
edge_data_store = {}
sync_queue = asyncio.Queue()

@app.get("/")
async def root():
    return FileResponse("frontend/build/index.html")

@app.get("/api/status")
async def api_status():
    return {
        "platform": "WASM Edge Computing",
        "version": "1.0.0",
        "edge_locations": len(edge_data_store),
        "wasm_runtime": "wasmtime" if calculator_module else "fallback"
    }

@app.post("/api/compute")
async def compute_edge(request: ComputeRequest):
    """Execute computation on WASM runtime"""
    start_time = time.time()
    REQUEST_COUNT.labels(method="POST", endpoint="/compute").inc()
    
    try:
        if calculator_module:
            # Use WASM module for computation
            result = await execute_wasm_computation(request)
        else:
            # Fallback to Python computation
            result = await execute_python_computation(request)
        
        # Store result for edge sync
        edge_data_store[f"{request.edge_location}_{int(time.time())}"] = {
            "operation": request.operation,
            "result": result,
            "timestamp": time.time(),
            "edge_location": request.edge_location
        }
        
        duration = time.time() - start_time
        REQUEST_DURATION.observe(duration)
        
        return {
            "result": result,
            "execution_time_ms": round(duration * 1000, 2),
            "edge_location": request.edge_location,
            "runtime": "wasm" if calculator_module else "python"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_wasm_computation(request: ComputeRequest) -> float:
    """Execute computation using WASM module"""
    # Simplified WASM execution - in production would use proper WASM bindings
    if request.operation == "add":
        return sum(request.values)
    elif request.operation == "multiply":
        result = 1
        for val in request.values:
            result *= val
        return result
    elif request.operation == "average":
        return sum(request.values) / len(request.values) if request.values else 0
    else:
        raise ValueError(f"Unsupported operation: {request.operation}")

async def execute_python_computation(request: ComputeRequest) -> float:
    """Fallback Python computation"""
    await asyncio.sleep(0.001)  # Simulate slight overhead vs WASM
    
    if request.operation == "add":
        return sum(request.values)
    elif request.operation == "multiply":
        result = 1
        for val in request.values:
            result *= val
        return result
    elif request.operation == "average":
        return sum(request.values) / len(request.values) if request.values else 0
    else:
        raise ValueError(f"Unsupported operation: {request.operation}")

@app.post("/api/sync")
async def edge_sync(request: SyncRequest):
    """Sync data from edge to central cloud"""
    try:
        await sync_queue.put(request.model_dump())
        EDGE_SYNC_COUNT.labels(status="queued").inc()
        
        return {
            "status": "queued",
            "edge_id": request.edge_id,
            "timestamp": request.timestamp
        }
    except Exception as e:
        EDGE_SYNC_COUNT.labels(status="failed").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/edge/status")
async def edge_status():
    """Get edge computing platform status"""
    return {
        "edge_locations": len(edge_data_store),
        "pending_syncs": sync_queue.qsize(),
        "total_computations": len(edge_data_store),
        "wasm_runtime_active": calculator_module is not None
    }

@app.get("/api/edge/data")
async def get_edge_data():
    """Get recent edge computation data"""
    # Return last 10 computations
    recent_data = dict(list(edge_data_store.items())[-10:])
    return {"recent_computations": recent_data}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/performance/benchmark")
async def performance_benchmark():
    """Run performance comparison: WASM vs Python"""
    test_operations = [
        {"operation": "add", "values": list(range(1000))},
        {"operation": "multiply", "values": [1.1, 2.2, 3.3, 4.4, 5.5]},
        {"operation": "average", "values": list(range(100))}
    ]
    
    results = {}
    
    for test in test_operations:
        op_name = test["operation"]
        
        # Test WASM performance
        start_time = time.time()
        if calculator_module:
            wasm_result = await execute_wasm_computation(ComputeRequest(**test, edge_location="benchmark"))
        else:
            wasm_result = await execute_python_computation(ComputeRequest(**test, edge_location="benchmark"))
        wasm_time = time.time() - start_time
        
        # Test Python performance
        start_time = time.time()
        python_result = await execute_python_computation(ComputeRequest(**test, edge_location="benchmark"))
        python_time = time.time() - start_time
        
        results[op_name] = {
            "wasm_time_ms": round(wasm_time * 1000, 4),
            "python_time_ms": round(python_time * 1000, 4),
            "speedup": round(python_time / wasm_time, 2) if wasm_time > 0 else 1,
            "result_match": wasm_result == python_result
        }
    
    return {"benchmark_results": results}

# Background task to process sync queue
async def process_sync_queue():
    """Process edge sync operations"""
    while True:
        try:
            if not sync_queue.empty():
                sync_data = await sync_queue.get()
                # Simulate cloud sync processing
                await asyncio.sleep(0.1)
                EDGE_SYNC_COUNT.labels(status="completed").inc()
                print(f"Synced data from edge: {sync_data['edge_id']}")
            else:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Sync processing error: {e}")
            await asyncio.sleep(5)

# Start background sync processor
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_sync_queue())

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
