from fastapi import APIRouter, HTTPException

router = APIRouter()

optimizer = None

def set_optimizer(o):
    global optimizer
    optimizer = o

@router.get("/recommendations")
async def get_recommendations():
    """Get query optimization recommendations"""
    if not optimizer:
        raise HTTPException(status_code=503, detail="Optimizer not initialized")
    
    return optimizer.get_recommendations()
