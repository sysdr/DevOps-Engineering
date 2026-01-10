from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

class CostSummary(BaseModel):
    total: float
    currency: str = "USD"
    period: str
    timestamp: datetime

class NamespaceCost(BaseModel):
    namespace: str
    cost: float
    percentage: float
    trend: str  # up, down, stable
