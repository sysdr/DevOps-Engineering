from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import json
import threading
import sys
import os
from kafka import KafkaConsumer

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.models.notification import NotificationCreate, Notification, NotificationType
from shared.utils.health_check import HealthChecker

app = FastAPI(title="Notification Service", version="1.0.0")

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./notifications.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class NotificationDB(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    type = Column(String)
    title = Column(String)
    message = Column(String)
    meta_data = Column(JSON)
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize services
health_checker = HealthChecker("notification-service")

# Event consumer
def start_event_consumer():
    try:
        consumer = KafkaConsumer(
            'user-events',
            'order-events',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        print("Starting Kafka consumer...")
        for message in consumer:
            process_event(message.value)
    except Exception as e:
        print(f"Kafka consumer error: {e}")

def process_event(event_data):
    db = SessionLocal()
    try:
        event_type = event_data.get('event_type')
        data = event_data.get('data', {})
        
        if event_type == 'user.created':
            notification = NotificationDB(
                user_id=data.get('user_id'),
                type=NotificationType.EMAIL.value,
                title="Welcome!",
                message=f"Welcome {data.get('full_name')}! Your account has been created successfully.",
                meta_data={"event_id": event_data.get('event_id')}
            )
            db.add(notification)
            db.commit()
            print(f"Created welcome notification for user {data.get('user_id')}")
            
        elif event_type == 'order.created':
            notification = NotificationDB(
                user_id=data.get('user_id'),
                type=NotificationType.EMAIL.value,
                title="Order Confirmation",
                message=f"Your order #{data.get('order_id')} has been created for ${data.get('total_amount')}",
                meta_data={"order_id": data.get('order_id'), "event_id": event_data.get('event_id')}
            )
            db.add(notification)
            db.commit()
            print(f"Created order notification for user {data.get('user_id')}")
            
    except Exception as e:
        print(f"Error processing event: {e}")
    finally:
        db.close()

# Start consumer in background thread
consumer_thread = threading.Thread(target=start_event_consumer, daemon=True)
consumer_thread.start()

@app.get("/health")
async def health_check():
    return health_checker.get_health_status()

@app.get("/")
async def root():
    return {"message": "Notification Service is running"}

@app.get("/notifications/")
async def get_notifications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    notifications = db.query(NotificationDB).offset(skip).limit(limit).all()
    return [
        {
            "id": notif.id,
            "user_id": notif.user_id,
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "metadata": notif.meta_data,
            "sent": notif.sent,
            "created_at": notif.created_at
        } for notif in notifications
    ]

@app.get("/notifications/user/{user_id}")
async def get_user_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(NotificationDB).filter(NotificationDB.user_id == user_id).all()
    return [
        {
            "id": notif.id,
            "user_id": notif.user_id,
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "metadata": notif.meta_data,
            "sent": notif.sent,
            "created_at": notif.created_at
        } for notif in notifications
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
