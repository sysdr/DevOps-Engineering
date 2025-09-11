import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from app import app, KubernetesManager

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_k8s_client():
    with patch('app.client') as mock_client:
        yield mock_client

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data

def test_cluster_info_endpoint(client, mock_k8s_client):
    """Test cluster info endpoint"""
    # Mock Kubernetes API responses
    mock_nodes = Mock()
    mock_nodes.items = [
        Mock(
            metadata=Mock(
                name='node-1',
                labels={'node.kubernetes.io/instance-type': 't3.medium'}
            ),
            status=Mock(
                conditions=[Mock(type='Ready', status='True')],
                capacity={'cpu': '2', 'memory': '4Gi', 'pods': '110'}
            )
        )
    ]
    
    mock_pods = Mock()
    mock_pods.items = [
        Mock(status=Mock(phase='Running')),
        Mock(status=Mock(phase='Pending'))
    ]
    
    mock_namespaces = Mock()
    mock_namespaces.items = [Mock(), Mock(), Mock()]
    
    with patch('app.k8s_manager.v1.list_node', return_value=mock_nodes), \
         patch('app.k8s_manager.v1.list_pod_for_all_namespaces', return_value=mock_pods), \
         patch('app.k8s_manager.v1.list_namespace', return_value=mock_namespaces):
        
        response = client.get('/api/cluster/info')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'nodes' in data
        assert 'pods' in data
        assert 'namespaces' in data
        assert data['nodes']['total'] == 1
        assert data['pods']['running'] == 1
        assert data['pods']['pending'] == 1

def test_autoscaling_status_endpoint(client):
    """Test autoscaling status endpoint"""
    mock_hpas = Mock()
    mock_hpas.items = []
    
    with patch('app.k8s_manager.autoscaling_v1.list_horizontal_pod_autoscaler_for_all_namespaces', return_value=mock_hpas):
        response = client.get('/api/autoscaling/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'hpas' in data
        assert 'cluster_autoscaler' in data

def test_network_policies_endpoint(client):
    """Test network policies endpoint"""
    mock_policies = {
        'items': [
            {
                'metadata': {'name': 'deny-all', 'namespace': 'default'},
                'spec': {
                    'podSelector': {},
                    'ingress': [],
                    'egress': []
                }
            }
        ]
    }
    
    with patch('app.k8s_manager.metrics_v1.list_cluster_custom_object', return_value=mock_policies):
        response = client.get('/api/network/policies')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'policies' in data
        assert 'total' in data
        assert data['total'] == 1

def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'http_requests_total' in response.data

class TestKubernetesManager:
    """Test KubernetesManager class"""
    
    @patch('app.config.load_incluster_config')
    def test_init_incluster(self, mock_load_incluster):
        """Test initialization with in-cluster config"""
        KubernetesManager()
        mock_load_incluster.assert_called_once()
    
    @patch('app.config.load_incluster_config')
    @patch('app.config.load_kube_config')
    def test_init_kubeconfig_fallback(self, mock_load_kube, mock_load_incluster):
        """Test initialization fallback to kubeconfig"""
        mock_load_incluster.side_effect = Exception("Not in cluster")
        KubernetesManager()
        mock_load_kube.assert_called_once()

if __name__ == '__main__':
    pytest.main([__file__])
