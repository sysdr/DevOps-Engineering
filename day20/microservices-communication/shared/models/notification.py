from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    title: str
    message: str
    metadata: dict = {}

class Notification(NotificationCreate):
    id: int
    sent: bool = False
    created_at: datetime

