import pytest
import yaml
import tempfile
import subprocess
import time

def test_crd_valid():
    """Test that CRD is valid Kubernetes YAML"""
    with open('k8s-manifests/webapp-crd.yaml', 'r') as f:
        crd = yaml.safe_load(f)
    
    assert crd['kind'] == 'CustomResourceDefinition'
    assert crd['spec']['group'] == 'platform.devops'
    assert 'webapps' in crd['spec']['names']['plural']

def test_rbac_valid():
    """Test RBAC configuration is valid"""
    with open('k8s-manifests/rbac.yaml', 'r') as f:
        docs = list(yaml.safe_load_all(f))
    
    assert len(docs) == 3  # ServiceAccount, ClusterRole, ClusterRoleBinding
    assert docs[0]['kind'] == 'ServiceAccount'
    assert docs[1]['kind'] == 'ClusterRole'
    assert docs[2]['kind'] == 'ClusterRoleBinding'

def test_resource_quota_valid():
    """Test resource quota configuration"""
    with open('k8s-manifests/resource-quota.yaml', 'r') as f:
        quota = yaml.safe_load(f)
    
    assert quota['kind'] == 'ResourceQuota'
    assert 'requests.cpu' in quota['spec']['hard']
    assert 'requests.memory' in quota['spec']['hard']
