import pytest
import requests
import time
import subprocess
import json

BASE_URL = "http://localhost:8080"

def test_health_checks():
    """Test all service health endpoints"""
    services = ["users", "products", "orders", "recommendations"]
    
    for service in services:
        try:
            response = requests.get(f"{BASE_URL}/{service}/health", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            print(f"✅ {service} health check passed")
        except Exception as e:
            print(f"❌ {service} health check failed: {e}")
            assert False, f"Health check failed for {service}"

def test_user_service():
    """Test user service functionality"""
    # Get all users
    response = requests.get(f"{BASE_URL}/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) > 0
    
    # Get specific user
    user_id = users[0]["id"]
    response = requests.get(f"{BASE_URL}/users/{user_id}")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == user_id
    print("✅ User service tests passed")

def test_product_service():
    """Test product service functionality"""
    # Get all products
    response = requests.get(f"{BASE_URL}/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) > 0
    
    # Get specific product
    product_id = products[0]["id"]
    response = requests.get(f"{BASE_URL}/products/{product_id}")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == product_id
    print("✅ Product service tests passed")

def test_order_service():
    """Test order service functionality"""
    # Create an order
    order_data = {
        "user_id": 1,
        "items": [{"product_id": 1, "quantity": 2}]
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=order_data)
    assert response.status_code == 200
    order = response.json()
    assert order["user_id"] == 1
    assert len(order["items"]) == 1
    
    # Get the created order
    order_id = order["id"]
    response = requests.get(f"{BASE_URL}/orders/{order_id}")
    assert response.status_code == 200
    print("✅ Order service tests passed")

def test_recommendation_service():
    """Test recommendation service functionality"""
    response = requests.get(f"{BASE_URL}/recommendations/1")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert data["user_id"] == 1
    print("✅ Recommendation service tests passed")

def test_istio_metrics():
    """Test Istio observability"""
    # Check if Istio proxy is injected
    result = subprocess.run(
        ["kubectl", "get", "pods", "-o", "json"],
        capture_output=True, text=True
    )
    pods_data = json.loads(result.stdout)
    
    # Find application pods and check for istio-proxy container
    app_pods = [pod for pod in pods_data["items"] 
               if pod["metadata"]["name"].startswith(("user-service", "product-service"))]
    
    assert len(app_pods) > 0, "No application pods found"
    
    for pod in app_pods:
        containers = [c["name"] for c in pod["spec"]["containers"]]
        assert "istio-proxy" in containers, f"Istio proxy not found in pod {pod['metadata']['name']}"
    
    print("✅ Istio sidecar injection verified")

def test_circuit_breaker():
    """Test circuit breaker functionality"""
    # Make multiple requests to trigger potential failures
    success_count = 0
    total_requests = 20
    
    for _ in range(total_requests):
        try:
            response = requests.get(f"{BASE_URL}/products/1", timeout=5)
            if response.status_code == 200:
                success_count += 1
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.1)
    
    # Should have some successful requests even with failures
    assert success_count > 0, "Circuit breaker may not be working correctly"
    print(f"✅ Circuit breaker test passed: {success_count}/{total_requests} requests successful")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
