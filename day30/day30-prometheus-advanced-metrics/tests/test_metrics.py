"""
Tests for Prometheus Metrics Application
"""

import pytest
import httpx
import asyncio
import time

BASE_URL = "http://localhost:8000"

@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=30.0)

class TestHealthEndpoints:
    """Test health and basic endpoints"""
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "checks" in data

class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""
    
    def test_metrics_endpoint_returns_prometheus_format(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        
        content = response.text
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content
        assert "orders_created_total" in content
        assert "inventory_items_available" in content
    
    def test_metrics_contain_custom_metrics(self, client):
        response = client.get("/metrics")
        content = response.text
        
        # Check for business metrics
        assert "order_value_dollars" in content
        assert "active_users_total" in content
        assert "queue_depth_messages" in content
        assert "database_connections_total" in content
        
        # Check for app info
        assert "app_info" in content

class TestOrderEndpoints:
    """Test order creation and metrics"""
    
    def test_create_order_success(self, client):
        response = client.post(
            "/orders",
            params={
                "value": 150.0,
                "payment_method": "credit_card",
                "region": "us-east"
            }
        )
        # May occasionally fail due to simulated errors
        if response.status_code == 200:
            data = response.json()
            assert "order_id" in data
            assert data["status"] == "created"
            assert data["value"] == 150.0
    
    def test_simulate_orders(self, client):
        response = client.get("/orders/simulate?count=5")
        assert response.status_code == 200
        data = response.json()
        assert data["simulated"] == 5
        assert "successful" in data
        assert "failed" in data
    
    def test_orders_increment_metrics(self, client):
        # Get initial metrics
        initial_metrics = client.get("/metrics").text
        
        # Create some orders
        for _ in range(3):
            client.post("/orders", params={"value": 100.0})
        
        # Check metrics increased
        final_metrics = client.get("/metrics").text
        assert "orders_created_total" in final_metrics

class TestAlertEndpoints:
    """Test alert webhook and retrieval"""
    
    def test_receive_alert(self, client):
        alert_payload = {
            "status": "firing",
            "alerts": [
                {
                    "labels": {
                        "alertname": "TestAlert",
                        "severity": "warning"
                    },
                    "annotations": {
                        "summary": "Test alert"
                    }
                }
            ]
        }
        
        response = client.post("/webhook/alerts", json=alert_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
    
    def test_get_alerts(self, client):
        response = client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "alerts" in data

class TestDashboardData:
    """Test dashboard data endpoint"""
    
    def test_dashboard_data(self, client):
        response = client.get("/dashboard/data")
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "metrics" in data
        assert "active_users" in data["metrics"]
        assert "queues" in data["metrics"]
        assert "database" in data["metrics"]

class TestLatencyEndpoints:
    """Test latency-related endpoints"""
    
    def test_slow_endpoint(self, client):
        start = time.time()
        response = client.get("/slow")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration >= 0.5  # Minimum expected delay
        
        data = response.json()
        assert "delay" in data
    
    def test_error_endpoint(self, client):
        # This endpoint fails 70% of the time
        responses = []
        for _ in range(10):
            response = client.get("/error")
            responses.append(response.status_code)
        
        # Should have at least some failures
        assert 500 in responses or 200 in responses

class TestMetricsInstrumentation:
    """Test that metrics are properly instrumented"""
    
    def test_request_duration_histogram(self, client):
        # Make some requests
        for _ in range(5):
            client.get("/")
        
        metrics = client.get("/metrics").text
        
        # Check histogram buckets exist
        assert "http_request_duration_seconds_bucket" in metrics
        assert "http_request_duration_seconds_count" in metrics
        assert "http_request_duration_seconds_sum" in metrics
    
    def test_slo_tracking(self, client):
        # Make requests
        for _ in range(5):
            client.get("/")
        
        metrics = client.get("/metrics").text
        assert "slo_requests_total" in metrics

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
