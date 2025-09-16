from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os

app = FastAPI(title="User Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    id: int
    name: str
    email: str
    role: str
    active: bool

class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "user"

# Mock database
users_db = [
    User(id=1, name="John Doe", email="john@example.com", role="admin", active=True),
    User(id=2, name="Jane Smith", email="jane@example.com", role="user", active=True),
    User(id=3, name="Bob Wilson", email="bob@example.com", role="user", active=False)
]

@app.get("/")
async def root():
    return {
        "service": "user-service",
        "version": "1.0.0",
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "status": "healthy"
    }

@app.get("/users", response_model=List[User])
async def get_users():
    return users_db

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    new_id = max([u.id for u in users_db]) + 1 if users_db else 1
    new_user = User(
        id=new_id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=True
    )
    users_db.append(new_user)
    return new_user

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user"}

@app.get("/stats")
async def get_stats():
    active_users = len([u for u in users_db if u.active])
    return {
        "total_users": len(users_db),
        "active_users": active_users,
        "inactive_users": len(users_db) - active_users
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
