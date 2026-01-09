from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()

# These will be set by main.py
profiler = None

def set_profiler(p):
    global profiler
    profiler = p

@router.get("/flame-graph")
async def get_flame_graph():
    """Get flame graph data"""
    if not profiler:
        raise HTTPException(status_code=503, detail="Profiler not initialized")
    
    return profiler.get_flame_graph_data()

@router.get("/hotspots")
async def get_hotspots():
    """Get current CPU hotspots"""
    if not profiler:
        raise HTTPException(status_code=503, detail="Profiler not initialized")
    
    return {
        'hotspots': profiler.hotspots,
        'timestamp': datetime.utcnow().isoformat()
    }

@router.post("/test/cpu-intensive")
async def test_cpu_intensive():
    """Trigger CPU-intensive operation for testing"""
    # Simulate CPU load
    result = sum(i ** 2 for i in range(1000000))
    return {'result': 'CPU intensive operation completed', 'sum': result}
