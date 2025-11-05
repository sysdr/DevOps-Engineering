"""
Tests for Secrets Manager
"""
import sys
import base64
sys.path.append('../backend')

from secrets_manager import ExternalSecretsSimulator, SealedSecretsSimulator


def test_external_secrets():
    """Test External Secrets Operator simulation"""
    eso = ExternalSecretsSimulator()
    
    # Create external secret
    eso.create_external_secret('test-db', 'default', 'prod/db/password')
    
    # Check that Kubernetes secret was created
    assert 'default/test-db' in eso.kubernetes_secrets
    
    secret = eso.kubernetes_secrets['default/test-db']
    assert secret['metadata']['name'] == 'test-db'
    assert secret['metadata']['labels']['managed-by'] == 'external-secrets'
    
    # Decode and verify secret value
    password_b64 = secret['data']['password']
    password = base64.b64decode(password_b64).decode()
    assert password == 'super-secret-db-password-2024'
    
    print("✓ External Secrets test passed")


def test_sealed_secrets():
    """Test Sealed Secrets simulation"""
    ss = SealedSecretsSimulator()
    
    # Get public certificate
    cert = ss.get_public_cert()
    assert '-----BEGIN PUBLIC KEY-----' in cert
    
    # Seal a secret
    secret_data = {
        'username': 'testuser',
        'password': 'testpass'
    }
    
    sealed = ss.seal_secret('default', 'my-secret', secret_data)
    assert sealed['kind'] == 'SealedSecret'
    assert 'encryptedData' in sealed['spec']
    
    # Verify encryption (should be different from original)
    encrypted_password = sealed['spec']['encryptedData']['password']
    assert encrypted_password != base64.b64encode(b'testpass').decode()
    
    # Unseal and verify
    unsealed = ss.unseal_secret(sealed)
    assert unsealed['kind'] == 'Secret'
    
    # Decode and verify
    unsealed_password = base64.b64decode(unsealed['data']['password']).decode()
    assert unsealed_password == 'testpass'
    
    print("✓ Sealed Secrets test passed")


def test_secret_status():
    """Test secret status tracking"""
    eso = ExternalSecretsSimulator()
    eso.create_external_secret('db-creds', 'prod', 'prod/db/password')
    eso.create_external_secret('api-key', 'prod', 'prod/api/key')
    
    statuses = eso.get_secret_status()
    assert len(statuses) == 2
    
    for status in statuses:
        assert status.secret_type == 'external'
        assert status.sync_status == 'synced'
        assert status.source is not None
    
    print("✓ Secret status test passed")


def run_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("Running Secrets Manager Tests")
    print("="*50 + "\n")
    
    test_external_secrets()
    test_sealed_secrets()
    test_secret_status()
    
    print("\n" + "="*50)
    print("All Secrets Manager Tests Passed! ✓")
    print("="*50)


if __name__ == '__main__':
    run_tests()
