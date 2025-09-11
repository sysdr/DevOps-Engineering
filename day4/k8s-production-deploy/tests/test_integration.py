import pytest
import requests
import time
import subprocess
import json

class TestIntegration:
    """Integration tests for the complete application"""
    
    @pytest.fixture(scope="class")
    def backend_url(self):
        """Backend service URL"""
        return "http://localhost:5000"
    
    @pytest.fixture(scope="class")
    def frontend_url(self):
        """Frontend service URL"""
        return "http://localhost:3000"
    
    def test_backend_health(self, backend_url):
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{backend_url}/health", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not running - run 'bash start.sh' first")
    
    def test_cluster_info_api(self, backend_url):
        """Test cluster info API"""
        try:
            response = requests.get(f"{backend_url}/api/cluster/info", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert 'nodes' in data
            assert 'pods' in data
            assert 'namespaces' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not running - run 'bash start.sh' first")
    
    def test_autoscaling_api(self, backend_url):
        """Test autoscaling API"""
        try:
            response = requests.get(f"{backend_url}/api/autoscaling/status", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert 'hpas' in data
            assert 'cluster_autoscaler' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not running - run 'bash start.sh' first")
    
    def test_network_policies_api(self, backend_url):
        """Test network policies API"""
        try:
            response = requests.get(f"{backend_url}/api/network/policies", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert 'policies' in data
            assert 'total' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not running - run 'bash start.sh' first")
    
    def test_prometheus_metrics(self, backend_url):
        """Test Prometheus metrics endpoint"""
        try:
            response = requests.get(f"{backend_url}/metrics", timeout=10)
            assert response.status_code == 200
            assert 'http_requests_total' in response.text
            assert 'http_request_duration_seconds' in response.text
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not running - run 'bash start.sh' first")
    
    def test_frontend_loads(self, frontend_url):
        """Test frontend application loads"""
        try:
            response = requests.get(frontend_url, timeout=10)
            assert response.status_code == 200
            assert 'Kubernetes Production Dashboard' in response.text
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend not running - run 'bash start.sh' first")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
