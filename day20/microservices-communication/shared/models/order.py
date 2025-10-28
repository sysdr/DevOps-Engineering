from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItem(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItem]
    total_amount: float

class Order(OrderCreate):
    id: int
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime

class OrderResponse(BaseModel):
    id: int
    user_id: int
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus
    created_at: datetime

class OrderEvent(BaseModel):
    order_id: int
    event_type: str
    data: dict
    timestamp: datetime
