import pytest
import requests
import time
import subprocess
import signal
import os

class TestIntegration:
    """Integration tests for GitOps dashboard"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Start and stop the Flask application"""
        # Start the application
        self.process = subprocess.Popen(
            ['python', 'web-dashboard/app.py'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)  # Wait for server to start
        
        yield
        
        # Stop the application
        self.process.terminate()
        self.process.wait()
    
    def test_dashboard_integration(self):
        """Test full dashboard integration"""
        response = requests.get('http://localhost:5000/')
        assert response.status_code == 200
        assert 'Advanced GitOps Dashboard' in response.text
    
    def test_api_integration(self):
        """Test API endpoints integration"""
        response = requests.get('http://localhost:5000/api/status')
        assert response.status_code == 200
        
        data = response.json()
        assert 'applications' in data
        assert 'rollouts' in data
        assert 'applicationsets' in data
    
    def test_health_check_integration(self):
        """Test health check integration"""
        response = requests.get('http://localhost:5000/health')
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
