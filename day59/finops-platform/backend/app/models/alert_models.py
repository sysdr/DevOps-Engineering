from pydantic import BaseModel
from datetime import datetime

class Alert(BaseModel):
    id: str
    timestamp: datetime
    severity: str
    namespace: str
    message: str
    acknowledged: bool = False
