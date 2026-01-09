from fastapi import APIRouter, HTTPException

router = APIRouter()

planner = None

def set_planner(p):
    global planner
    planner = p

@router.get("/runway")
async def get_runway():
    """Get capacity runway report"""
    if not planner:
        raise HTTPException(status_code=503, detail="Capacity planner not initialized")
    
    return planner.get_capacity_report()
