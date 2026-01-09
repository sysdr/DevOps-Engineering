from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()

scaler = None

def set_scaler(s):
    global scaler
    scaler = s

@router.get("/forecast")
async def get_forecast():
    """Get load forecast"""
    if not scaler:
        raise HTTPException(status_code=503, detail="Scaler not initialized")
    
    return scaler.get_forecast()

@router.get("/status")
async def get_status():
    """Get scaling status"""
    if not scaler:
        raise HTTPException(status_code=503, detail="Scaler not initialized")
    
    return scaler.get_scaling_status()

# Note: /events route is handled directly in main.py to avoid conflicts
