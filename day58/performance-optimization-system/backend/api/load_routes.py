from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoadPattern(BaseModel):
    pattern: str
    duration: int = 300

@router.post("/generate")
async def generate_load(config: LoadPattern):
    """Generate load for testing"""
    valid_patterns = ['steady', 'spike', 'ramp']
    
    if config.pattern not in valid_patterns:
        raise HTTPException(status_code=400, detail=f"Invalid pattern. Use: {valid_patterns}")
    
    # In production, this would trigger actual load generation
    return {
        'status': 'load_generation_started',
        'pattern': config.pattern,
        'duration': config.duration
    }
