from pydantic import BaseModel
from typing import Dict, Optional

class Recommendation(BaseModel):
    id: str
    type: str
    resource: str
    savings_monthly: float
    confidence: float
    reason: str

class CommitmentPlan(BaseModel):
    instance_type: str
    quantity: int
    term: str
    upfront_cost: float
    monthly_savings: float
    payback_months: float
