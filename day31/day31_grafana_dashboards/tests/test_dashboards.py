import pytest
import json
import requests
from pathlib import Path
import time

BASE_URL = "http://localhost:8001"
GRAFANA_URL = "http://localhost:3000"
METRICS_URL = "http://localhost:8000"

def test_backend_health():
    """Test backend API is running"""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Dashboard Management API"

def test_metrics_service():
    """Test metrics service is running"""
    response = requests.get(f"{METRICS_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "metrics_endpoint" in data

def test_prometheus_metrics():
    """Test Prometheus metrics endpoint"""
    response = requests.get(f"{METRICS_URL}/metrics")
    assert response.status_code == 200
    content = response.text
    assert "business_active_users" in content
    assert "business_user_registrations_total" in content
    assert "business_order_processing_seconds" in content

def test_grafana_health():
    """Test Grafana is accessible"""
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                assert data.get("database") == "ok"
                return
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(2)
                continue
            raise

def test_dashboard_list():
    """Test dashboard listing"""
    response = requests.get(f"{BASE_URL}/api/dashboards")
    assert response.status_code == 200
    data = response.json()
    assert "dashboards" in data
    assert "count" in data

def test_template_list():
    """Test template listing"""
    response = requests.get(f"{BASE_URL}/api/templates")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert data["count"] >= 0

def test_dashboard_json_structure():
    """Test dashboard JSON files are valid"""
    dashboard_dir = Path("grafana/dashboards")
    if dashboard_dir.exists():
        for json_file in dashboard_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)
                assert "dashboard" in data
                dashboard = data["dashboard"]
                assert "title" in dashboard
                assert "panels" in dashboard

def test_grafana_status_endpoint():
    """Test Grafana status endpoint"""
    response = requests.get(f"{BASE_URL}/api/grafana/status")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data or "status" in data

def test_metrics_generate_data():
    """Test metrics are being generated"""
    response1 = requests.get(f"{METRICS_URL}/metrics")
    time.sleep(1)
    response2 = requests.get(f"{METRICS_URL}/metrics")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    # Metrics should be present in both responses
    assert len(response1.text) > 100
    assert len(response2.text) > 100

def test_cors_headers():
    """Test CORS is properly configured"""
    response = requests.options(
        f"{BASE_URL}/api/dashboards",
        headers={"Origin": "http://localhost:3001"}
    )
    # FastAPI CORS should handle this
    assert response.status_code in [200, 204]

if __name__ == "__main__":
    print("Running dashboard tests...")
    pytest.main([__file__, "-v"])
