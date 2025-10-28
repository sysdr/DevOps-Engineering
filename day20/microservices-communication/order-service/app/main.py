from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.models.order import OrderCreate, OrderResponse, OrderStatus
from shared.models.events import DomainEvent, EventType
from shared.utils.event_publisher import EventPublisher
from shared.utils.health_check import HealthChecker

app = FastAPI(title="Order Service", version="1.0.0")

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./orders.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class OrderDB(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    items = Column(JSON)
    total_amount = Column(Float)
    status = Column(String, default=OrderStatus.PENDING.value)
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
health_checker = HealthChecker("order-service")
event_publisher = EventPublisher()

@app.get("/health")
async def health_check():
    return health_checker.get_health_status()

@app.get("/")
async def root():
    return {"message": "Order Service is running"}

@app.get("/orders/")
async def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = db.query(OrderDB).offset(skip).limit(limit).all()
    return [
        OrderResponse(
            id=order.id,
            user_id=order.user_id,
            items=order.items,
            total_amount=order.total_amount,
            status=OrderStatus(order.status),
            created_at=order.created_at
        ) for order in orders
    ]

@app.post("/orders/")
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Create new order
    db_order = OrderDB(
        user_id=order.user_id,
        items=[item.dict() for item in order.items],
        total_amount=order.total_amount,
        status=OrderStatus.PENDING.value
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Publish order created event
    event = DomainEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.ORDER_CREATED,
        aggregate_id=str(db_order.id),
        data={
            "order_id": db_order.id,
            "user_id": db_order.user_id,
            "total_amount": db_order.total_amount,
            "items": db_order.items
        },
        timestamp=datetime.utcnow(),
        correlation_id=str(uuid.uuid4())
    )
    
    try:
        await event_publisher.publish_event("order-events", event)
    except Exception as e:
        print(f"Failed to publish event: {e}")
    
    return OrderResponse(
        id=db_order.id,
        user_id=db_order.user_id,
        items=order.items,
        total_amount=db_order.total_amount,
        status=OrderStatus(db_order.status),
        created_at=db_order.created_at
    )

@app.get("/orders/{order_id}")
async def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        items=order.items,
        total_amount=order.total_amount,
        status=OrderStatus(order.status),
        created_at=order.created_at
    )

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: OrderStatus, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = order.status
    order.status = status.value
    db.commit()
    
    # Publish order status changed event
    event = DomainEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.ORDER_CONFIRMED if status == OrderStatus.CONFIRMED else EventType.ORDER_SHIPPED,
        aggregate_id=str(order.id),
        data={
            "order_id": order.id,
            "old_status": old_status,
            "new_status": status.value,
            "user_id": order.user_id
        },
        timestamp=datetime.utcnow(),
        correlation_id=str(uuid.uuid4())
    )
    
    try:
        await event_publisher.publish_event("order-events", event)
    except Exception as e:
        print(f"Failed to publish event: {e}")
    
    return {"message": f"Order {order_id} status updated to {status.value}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
