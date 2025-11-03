import pytest
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'web-dashboard'))

from app import app, GitOpsMonitor

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def monitor():
    return GitOpsMonitor()

def test_health_endpoint(client):
    """Test health endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data

def test_dashboard_endpoint(client):
    """Test dashboard renders successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Advanced GitOps Dashboard' in response.data

def test_api_status_endpoint(client):
    """Test API status endpoint"""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'applications' in data
    assert 'rollouts' in data
    assert 'applicationsets' in data

def test_applications_status(monitor):
    """Test applications status retrieval"""
    status = monitor.get_applications_status()
    assert isinstance(status, dict)
    assert 'app-of-apps' in status
    assert 'monitoring-stack' in status

def test_rollout_status(monitor):
    """Test rollout status retrieval"""
    status = monitor.get_rollout_status()
    assert isinstance(status, dict)
    assert 'sample-app-rollout' in status

def test_applicationset_status(monitor):
    """Test applicationset status retrieval"""
    status = monitor.get_applicationset_status()
    assert isinstance(status, dict)
    assert 'multi-env-applications' in status

class TestGitOpsManifests:
    """Test GitOps manifest structure"""
    
    def test_app_of_apps_manifest(self):
        """Test app-of-apps manifest structure"""
        with open('argocd-config/root-app/app-of-apps.yaml', 'r') as f:
            content = f.read()
            assert 'app-of-apps' in content
            assert 'argoproj.io/v1alpha1' in content
    
    def test_applicationset_manifest(self):
        """Test ApplicationSet manifest structure"""
        with open('applicationsets/multi-env-appset.yaml', 'r') as f:
            content = f.read()
            assert 'ApplicationSet' in content
            assert 'generators' in content
            assert 'template' in content
    
    def test_rollout_manifest(self):
        """Test Rollout manifest structure"""
        with open('rollouts/rollout-config.yaml', 'r') as f:
            content = f.read()
            assert 'Rollout' in content
            assert 'canary' in content
            assert 'steps' in content
