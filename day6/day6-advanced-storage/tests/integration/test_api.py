import pytest
import asyncio
import httpx
import time
import json

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

@pytest.mark.asyncio
async def test_users_crud_operations():
    """Test user creation and retrieval"""
    async with httpx.AsyncClient() as client:
        # Create user
        user_data = {
            "username": f"test_user_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com"
        }
        
        create_response = await client.post(f"{BASE_URL}/users", json=user_data)
        assert create_response.status_code == 200
        
        create_data = create_response.json()
        assert "id" in create_data
        assert create_data["status"] == "created"
        
        # Get users
        get_response = await client.get(f"{BASE_URL}/users")
        assert get_response.status_code == 200
        
        users = get_response.json()
        assert isinstance(users, list)
        assert any(user["username"] == user_data["username"] for user in users)

@pytest.mark.asyncio
async def test_transaction_creation():
    """Test transaction creation"""
    async with httpx.AsyncClient() as client:
        # First ensure we have a user
        user_data = {
            "username": f"transaction_user_{int(time.time())}",
            "email": f"trans_{int(time.time())}@example.com"
        }
        
        user_response = await client.post(f"{BASE_URL}/users", json=user_data)
        user_id = user_response.json()["id"]
        
        # Create transaction
        transaction_data = {
            "user_id": user_id,
            "amount": 100.50,
            "transaction_type": "deposit"
        }
        
        response = await client.post(f"{BASE_URL}/transactions", json=transaction_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["status"] == "created"

@pytest.mark.asyncio
async def test_database_stats():
    """Test database statistics endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/database/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "connections" in data
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_replication_status():
    """Test replication status endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/replication/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "primary_lsn" in data
        assert "replica" in data
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_dashboard_endpoint():
    """Test dashboard HTML endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
