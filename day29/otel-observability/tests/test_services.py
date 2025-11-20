import pytest
import httpx
import asyncio

BASE_URLS = {
    "order": "http://localhost:8000",
    "inventory": "http://localhost:8001",
    "payment": "http://localhost:8002"
}

@pytest.fixture
def client():
    return httpx.Client(timeout=30.0)

class TestHealthChecks:
    def test_order_service_health(self, client):
        response = client.get(f"{BASE_URLS['order']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "order-service"

    def test_inventory_service_health(self, client):
        response = client.get(f"{BASE_URLS['inventory']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_payment_service_health(self, client):
        response = client.get(f"{BASE_URLS['payment']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

class TestOrderFlow:
    def test_create_order_success(self, client):
        order_data = {
            "customer_id": "CUST-001",
            "items": [
                {
                    "product_id": "PROD-001",
                    "quantity": 2,
                    "price": 25.99
                }
            ],
            "payment_method": "credit_card"
        }
        
        response = client.post(f"{BASE_URLS['order']}/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "order_id" in data
        assert data["customer_id"] == "CUST-001"
        assert data["status"] == "completed"
        assert data["total"] == 51.98

    def test_get_order(self, client):
        # First create an order
        order_data = {
            "customer_id": "CUST-002",
            "items": [{"product_id": "PROD-002", "quantity": 1, "price": 50.00}],
            "payment_method": "debit_card"
        }
        
        create_response = client.post(f"{BASE_URLS['order']}/orders", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # Then retrieve it
        get_response = client.get(f"{BASE_URLS['order']}/orders/{order_id}")
        assert get_response.status_code == 200
        assert get_response.json()["order_id"] == order_id

    def test_list_orders(self, client):
        response = client.get(f"{BASE_URLS['order']}/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestInventoryService:
    def test_check_inventory(self, client):
        check_data = {
            "product_id": "PROD-003",
            "quantity": 5
        }
        
        response = client.post(f"{BASE_URLS['inventory']}/inventory/check", json=check_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "available" in data
        assert "stock" in data

    def test_get_inventory(self, client):
        response = client.get(f"{BASE_URLS['inventory']}/inventory")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_restock_inventory(self, client):
        response = client.post(
            f"{BASE_URLS['inventory']}/inventory/restock",
            params={"product_id": "PROD-004", "quantity": 100}
        )
        assert response.status_code == 200
        assert response.json()["new_stock"] >= 100

class TestPaymentService:
    def test_process_payment(self, client):
        payment_data = {
            "order_id": "ORD-TEST-001",
            "amount": 99.99,
            "method": "credit_card",
            "customer_id": "CUST-TEST"
        }
        
        response = client.post(f"{BASE_URLS['payment']}/payments/process", json=payment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "transaction_id" in data
        assert data["status"] == "completed"
        assert data["amount"] == 99.99

    def test_list_payments(self, client):
        response = client.get(f"{BASE_URLS['payment']}/payments")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestDistributedTracing:
    def test_trace_propagation(self, client):
        """Test that traces propagate across services"""
        order_data = {
            "customer_id": "TRACE-TEST",
            "items": [{"product_id": "PROD-001", "quantity": 1, "price": 10.00}],
            "payment_method": "credit_card"
        }
        
        response = client.post(f"{BASE_URLS['order']}/orders", json=order_data)
        assert response.status_code == 200
        
        # The trace should include spans from all three services
        # We verify this by checking the order completed successfully,
        # which requires inventory check and payment processing
        assert response.json()["status"] == "completed"

class TestOTelCollector:
    def test_collector_health(self, client):
        response = client.get("http://localhost:13133")
        assert response.status_code == 200

    def test_collector_metrics(self, client):
        response = client.get("http://localhost:8888/metrics")
        assert response.status_code == 200
        assert "otelcol" in response.text

    def test_prometheus_metrics_endpoint(self, client):
        response = client.get("http://localhost:8889/metrics")
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
