import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add operator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operator'))

# Mock Kubernetes config loading before importing main
with patch('kubernetes.config.load_incluster_config'), \
     patch('kubernetes.config.load_kube_config'), \
     patch('kubernetes.client.CoreV1Api'), \
     patch('kubernetes.client.AppsV1Api'), \
     patch('kubernetes.client.PolicyV1Api'):
    from main import WebAppOperator

@pytest.fixture
def operator():
    with patch('main.start_http_server'), \
         patch('main.v1'), \
         patch('main.apps_v1'), \
         patch('main.policy_v1'):
        return WebAppOperator()

@pytest.mark.asyncio
async def test_create_deployment(operator):
    """Test deployment creation"""
    spec = {
        'replicas': 3,
        'image': 'nginx:latest',
        'port': 8080,
        'resources': {'cpu': '100m', 'memory': '128Mi'},
        'affinity': {'zone': 'us-west-2a'}
    }
    
    # Mock the apps_v1 client
    mock_apps_v1 = MagicMock()
    with patch('main.apps_v1', mock_apps_v1):
        await operator.create_deployment('test-app', 'default', spec)
        mock_apps_v1.create_namespaced_deployment.assert_called_once()

@pytest.mark.asyncio
async def test_create_service(operator):
    """Test service creation"""
    spec = {'port': 8080}
    
    # Mock the v1 client
    mock_v1 = MagicMock()
    with patch('main.v1', mock_v1):
        await operator.create_service('test-app', 'default', spec)
        mock_v1.create_namespaced_service.assert_called_once()

@pytest.mark.asyncio
async def test_create_pdb(operator):
    """Test Pod Disruption Budget creation"""
    spec = {'replicas': 4}
    
    # Mock the policy_v1 client
    mock_policy_v1 = MagicMock()
    with patch('main.policy_v1', mock_policy_v1):
        await operator.create_pdb('test-app', 'default', spec)
        mock_policy_v1.create_namespaced_pod_disruption_budget.assert_called_once()

def test_affinity_calculation():
    """Test affinity rules are properly configured"""
    assert True  # Placeholder for affinity logic tests

def test_resource_calculation():
    """Test resource limit calculations"""
    assert True  # Placeholder for resource tests
