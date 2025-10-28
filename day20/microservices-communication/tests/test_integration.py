import pytest
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

class TestMicroservicesIntegration:
    
    @pytest.mark.asyncio
    async def test_user_creation_flow(self):
        """Test complete user creation and notification flow"""
        async with httpx.AsyncClient() as client:
            # Create user
            user_data = {
                "email": f"test_{datetime.now().timestamp()}@example.com",
                "full_name": "Test User",
                "is_active": True
            }
            
            response = await client.post(f"{BASE_URL}/users/", json=user_data)
            assert response.status_code == 200
            user = response.json()
            assert user["email"] == user_data["email"]
            
            # Wait a bit for async processing
            await asyncio.sleep(2)
            
            # Check if notification was created
            response = await client.get(f"{BASE_URL}/notifications/")
            assert response.status_code == 200
            notifications = response.json()
            
            user_notifications = [n for n in notifications if n["user_id"] == user["id"]]
            assert len(user_notifications) > 0
            assert "Welcome" in user_notifications[0]["title"]

    @pytest.mark.asyncio
    async def test_order_creation_flow(self):
        """Test complete order creation and notification flow"""
        async with httpx.AsyncClient() as client:
            # Create user first
            user_data = {
                "email": f"order_test_{datetime.now().timestamp()}@example.com",
                "full_name": "Order Test User",
                "is_active": True
            }
            
            response = await client.post(f"{BASE_URL}/users/", json=user_data)
            assert response.status_code == 200
            user = response.json()
            
            # Create order
            order_data = {
                "user_id": user["id"],
                "items": [{"product_id": 1, "quantity": 2, "price": 25.99}],
                "total_amount": 51.98
            }
            
            response = await client.post(f"{BASE_URL}/orders/", json=order_data)
            assert response.status_code == 200
            order = response.json()
            assert order["total_amount"] == 51.98
            
            # Wait for async processing
            await asyncio.sleep(2)
            
            # Check notifications
            response = await client.get(f"{BASE_URL}/notifications/")
            assert response.status_code == 200
            notifications = response.json()
            
            order_notifications = [n for n in notifications if n["user_id"] == user["id"] and "Order" in n["title"]]
            assert len(order_notifications) > 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_status(self):
        """Test circuit breaker status endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/circuit-breakers/")
            assert response.status_code == 200
            
            cb_status = response.json()
            assert "user-service" in cb_status
            assert "order-service" in cb_status
            assert "notification-service" in cb_status
            
            for service, status in cb_status.items():
                assert "state" in status
                assert "failure_count" in status
                assert status["state"] in ["closed", "open", "half_open"]

    @pytest.mark.asyncio
    async def test_service_health_checks(self):
        """Test all service health endpoints"""
        services = [
            ("Gateway", "http://localhost:8000/health"),
            ("User Service", "http://localhost:8001/health"),
            ("Order Service", "http://localhost:8002/health"),
            ("Notification Service", "http://localhost:8003/health")
        ]
        
        async with httpx.AsyncClient() as client:
            for service_name, health_url in services:
                try:
                    response = await client.get(health_url, timeout=5.0)
                    assert response.status_code == 200, f"{service_name} health check failed"
                    health_data = response.json()
                    assert "service" in health_data
                    assert health_data["status"] == "healthy"
                except httpx.ConnectError:
                    pytest.skip(f"{service_name} not running")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
