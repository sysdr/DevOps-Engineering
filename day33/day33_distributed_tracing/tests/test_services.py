import pytest
from httpx import AsyncClient
import sys
import os

# Add parent directory to path so we can import the service modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from order_service.main import app as order_app
from inventory_service.main import app as inventory_app
from payment_service.main import app as payment_app

@pytest.mark.asyncio
async def test_order_service_health():
    async with AsyncClient(app=order_app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_inventory_service_health():
    async with AsyncClient(app=inventory_app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_payment_service_health():
    async with AsyncClient(app=payment_app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_inventory_check():
    async with AsyncClient(app=inventory_app, base_url="http://test") as client:
        response = await client.post(
            "/inventory/check",
            json={"items": [{"product_id": "PROD-001", "quantity": 2}]}
        )
        assert response.status_code == 200
        assert response.json()["available"] == True

@pytest.mark.asyncio
async def test_get_stock():
    async with AsyncClient(app=inventory_app, base_url="http://test") as client:
        response = await client.get("/inventory/PROD-001")
        assert response.status_code == 200
        assert response.json()["stock"] > 0
