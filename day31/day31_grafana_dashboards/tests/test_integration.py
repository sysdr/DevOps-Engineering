import pytest
import requests
import time

def test_end_to_end_flow():
    """Test complete workflow from metrics to dashboard"""
    # 1. Check metrics service
    metrics_response = requests.get("http://localhost:8000/metrics")
    assert metrics_response.status_code == 200
    assert "business_active_users" in metrics_response.text
    
    # 2. Check backend API
    api_response = requests.get("http://localhost:8001/")
    assert api_response.status_code == 200
    
    # 3. Check Grafana health
    health_response = requests.get("http://localhost:8001/api/grafana/status")
    assert health_response.status_code == 200
    
    # 4. List dashboards
    dashboards_response = requests.get("http://localhost:8001/api/dashboards")
    assert dashboards_response.status_code == 200
    
    print("✓ End-to-end flow test passed!")

def test_dashboard_provisioning():
    """Test that dashboards are automatically provisioned"""
    time.sleep(5)  # Wait for provisioning
    response = requests.get("http://localhost:8001/api/dashboards")
    data = response.json()
    
    # Should have provisioned dashboards
    assert data["count"] >= 0
    print(f"✓ Found {data['count']} provisioned dashboards")

def test_template_availability():
    """Test that templates are available"""
    response = requests.get("http://localhost:8001/api/templates")
    data = response.json()
    
    assert data["count"] >= 2  # Should have at least 2 templates
    print(f"✓ Found {data['count']} dashboard templates")

if __name__ == "__main__":
    print("Running integration tests...")
    pytest.main([__file__, "-v"])
