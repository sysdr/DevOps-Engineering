from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Dict, Any

class EventType(str, Enum):
    USER_CREATED = "user.created"
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_SHIPPED = "order.shipped"
    PAYMENT_PROCESSED = "payment.processed"

class DomainEvent(BaseModel):
    event_id: str
    event_type: EventType
    aggregate_id: str
    data: Dict[str, Any]
    timestamp: datetime
    version: int = 1
    correlation_id: str
