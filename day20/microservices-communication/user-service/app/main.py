from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.models.user import UserCreate, UserResponse
from shared.models.events import DomainEvent, EventType
from shared.utils.event_publisher import EventPublisher
from shared.utils.health_check import HealthChecker

app = FastAPI(title="User Service", version="1.0.0")

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
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
health_checker = HealthChecker("user-service")
event_publisher = EventPublisher()

@app.get("/health")
async def health_check():
    return health_checker.get_health_status()

@app.get("/")
async def root():
    return {"message": "User Service is running"}

@app.get("/users/")
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(UserDB).offset(skip).limit(limit).all()
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at
        ) for user in users
    ]

@app.post("/users/")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    db_user = UserDB(
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Publish user created event
    event = DomainEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.USER_CREATED,
        aggregate_id=str(db_user.id),
        data={
            "user_id": db_user.id,
            "email": db_user.email,
            "full_name": db_user.full_name
        },
        timestamp=datetime.utcnow(),
        correlation_id=str(uuid.uuid4())
    )
    
    try:
        await event_publisher.publish_event("user-events", event)
    except Exception as e:
        print(f"Failed to publish event: {e}")
    
    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        created_at=db_user.created_at
    )

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
