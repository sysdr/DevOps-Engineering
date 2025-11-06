"""
Unit tests for Policy as Code system
Tests policy evaluation, API endpoints, and remediation workflows
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend/src'))

from api.server import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    print("✓ Health check test passed")

def test_get_policies(client):
    """Test policies endpoint"""
    response = client.get('/api/policies')
    assert response.status_code == 200
    data = response.get_json()
    assert 'policies' in data
    assert len(data['policies']) > 0
    print(f"✓ Policies test passed - found {len(data['policies'])} policies")

def test_get_violations(client):
    """Test violations endpoint"""
    response = client.get('/api/violations')
    assert response.status_code == 200
    data = response.get_json()
    assert 'violations' in data
    assert 'total' in data
    print(f"✓ Violations test passed - found {data['total']} violations")

def test_filter_violations_by_severity(client):
    """Test violation filtering by severity"""
    response = client.get('/api/violations?severity=critical')
    assert response.status_code == 200
    data = response.get_json()
    assert all(v['severity'] == 'critical' for v in data['violations'])
    print(f"✓ Severity filter test passed - {len(data['violations'])} critical violations")

def test_filter_violations_by_status(client):
    """Test violation filtering by status"""
    response = client.get('/api/violations?status=open')
    assert response.status_code == 200
    data = response.get_json()
    assert all(v['status'] == 'open' for v in data['violations'])
    print(f"✓ Status filter test passed - {len(data['violations'])} open violations")

def test_compliance_metrics(client):
    """Test compliance metrics calculation"""
    response = client.get('/api/compliance/metrics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'compliance_rate' in data
    assert 'total_resources' in data
    assert 'total_violations' in data
    assert 0 <= data['compliance_rate'] <= 100
    print(f"✓ Compliance metrics test passed - {data['compliance_rate']}% compliance")

def test_compliance_trends(client):
    """Test compliance trends endpoint"""
    response = client.get('/api/compliance/trends?days=7')
    assert response.status_code == 200
    data = response.get_json()
    assert 'trends' in data
    assert len(data['trends']) == 7
    print(f"✓ Trends test passed - {len(data['trends'])} days of data")

def test_remediate_violation(client):
    """Test violation remediation"""
    # First get a violation with remediation available
    response = client.get('/api/violations')
    violations = response.get_json()['violations']
    remediable = next((v for v in violations if v['remediation_available']), None)
    
    if remediable:
        response = client.post(f"/api/violations/{remediable['id']}/remediate")
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        print(f"✓ Remediation test passed - {data['message']}")
    else:
        print("⚠ No remediable violations found for testing")

def test_run_audit(client):
    """Test audit trigger"""
    response = client.post('/api/audit/run')
    assert response.status_code == 200
    data = response.get_json()
    assert 'scan_id' in data
    assert 'estimated_duration' in data
    print(f"✓ Audit test passed - Scan ID: {data['scan_id']}")

def test_invalid_violation_remediation(client):
    """Test remediation of non-existent violation"""
    response = client.post('/api/violations/invalid-id/remediate')
    assert response.status_code == 404
    print("✓ Invalid violation test passed")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
