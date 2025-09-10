import pytest
import json
from src.backend.api.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_metrics_endpoint(client):
    response = client.get('/api/metrics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'cpu' in data
    assert 'memory' in data

def test_containers_endpoint(client):
    response = client.get('/api/containers')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'containers' in data

def test_benchmark_endpoint(client):
    response = client.get('/api/benchmark')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'podman' in data
    assert 'docker' in data
