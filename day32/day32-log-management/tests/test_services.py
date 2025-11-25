import pytest
import httpx
import asyncio
from datetime import datetime

BASE_URLS = {
    'user': 'http://localhost:8001',
    'order': 'http://localhost:8002',
    'payment': 'http://localhost:8003'
}

@pytest.mark.asyncio
async def test_user_service_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URLS['user']}/health")
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'

@pytest.mark.asyncio
async def test_user_login_success():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URLS['user']}/api/login",
            json={"username": "alice", "password": "pass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert data['username'] == 'alice'

@pytest.mark.asyncio
async def test_user_login_failure():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URLS['user']}/api/login",
            json={"username": "alice", "password": "wrongpass"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_order_service_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URLS['order']}/health")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_order():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URLS['order']}/api/orders",
            json={
                "user_id": 1001,
                "items": [
                    {"product_id": 101, "quantity": 2, "price": 29.99},
                    {"product_id": 102, "quantity": 1, "price": 49.99}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert 'order_id' in data
        assert data['status'] == 'pending'

@pytest.mark.asyncio
async def test_payment_service_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URLS['payment']}/health")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_process_payment():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URLS['payment']}/api/payments",
            json={
                "order_id": 1001,
                "amount": 109.97,
                "payment_method": "credit_card"
            }
        )
        # May succeed or fail due to random scenarios
        assert response.status_code in [200, 402, 403, 504]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
