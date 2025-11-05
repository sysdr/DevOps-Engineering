"""
Secrets Management System - Handles External Secrets and Sealed Secrets
"""
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecretStatus:
    name: str
    namespace: str
    secret_type: str  # external, sealed, standard
    last_sync: str
    sync_status: str
    source: Optional[str]
    refresh_interval: Optional[str]


class ExternalSecretsSimulator:
    """Simulates External Secrets Operator functionality"""
    
    def __init__(self):
        self.secret_store = {
            'prod/db/password': 'super-secret-db-password-2024',
            'prod/api/key': 'api-key-xyz-789-secure',
            'prod/tls/cert': 'LS0tLS1CRUdJTi...',  # Base64 cert
        }
        self.external_secrets = []
        self.kubernetes_secrets = {}
        
    def create_external_secret(self, name: str, namespace: str, 
                               remote_key: str, refresh_interval: str = '1h'):
        """Create an ExternalSecret resource"""
        external_secret = {
            'apiVersion': 'external-secrets.io/v1beta1',
            'kind': 'ExternalSecret',
            'metadata': {
                'name': name,
                'namespace': namespace
            },
            'spec': {
                'refreshInterval': refresh_interval,
                'secretStoreRef': {
                    'name': 'aws-secret-store',
                    'kind': 'SecretStore'
                },
                'target': {
                    'name': name,
                    'creationPolicy': 'Owner'
                },
                'data': [{
                    'secretKey': 'password',
                    'remoteRef': {'key': remote_key}
                }]
            }
        }
        
        self.external_secrets.append(external_secret)
        logger.info(f"Created ExternalSecret: {namespace}/{name}")
        
        # Simulate sync
        self.sync_external_secret(external_secret)
        
    def sync_external_secret(self, external_secret: Dict):
        """Sync external secret from vault to Kubernetes"""
        name = external_secret['metadata']['name']
        namespace = external_secret['metadata']['namespace']
        remote_key = external_secret['spec']['data'][0]['remoteRef']['key']
        
        # Fetch from "vault"
        secret_value = self.secret_store.get(remote_key)
        
        if not secret_value:
            logger.error(f"Secret not found in vault: {remote_key}")
            return
        
        # Create Kubernetes Secret
        k8s_secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': name,
                'namespace': namespace,
                'labels': {
                    'managed-by': 'external-secrets'
                },
                'annotations': {
                    'last-sync': datetime.utcnow().isoformat(),
                    'source': remote_key
                }
            },
            'type': 'Opaque',
            'data': {
                'password': base64.b64encode(secret_value.encode()).decode()
            }
        }
        
        self.kubernetes_secrets[f"{namespace}/{name}"] = k8s_secret
        logger.info(f"Synced secret to Kubernetes: {namespace}/{name}")
    
    def get_secret_status(self) -> List[SecretStatus]:
        """Get status of all managed secrets"""
        statuses = []
        
        for key, secret in self.kubernetes_secrets.items():
            namespace, name = key.split('/')
            metadata = secret['metadata']
            
            status = SecretStatus(
                name=name,
                namespace=namespace,
                secret_type='external',
                last_sync=metadata['annotations'].get('last-sync', 'unknown'),
                sync_status='synced',
                source=metadata['annotations'].get('source'),
                refresh_interval='1h'
            )
            statuses.append(status)
        
        return statuses


class SealedSecretsSimulator:
    """Simulates Sealed Secrets controller functionality"""
    
    def __init__(self):
        # Generate RSA key pair for sealing/unsealing
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        self.sealed_secrets = []
        
    def get_public_cert(self) -> str:
        """Get public certificate for sealing secrets"""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()
    
    def seal_secret(self, namespace: str, name: str, secret_data: Dict[str, str]) -> Dict:
        """Seal a secret (encrypt with public key)"""
        # Encrypt each secret value
        encrypted_data = {}
        
        for key, value in secret_data.items():
            encrypted = self.public_key.encrypt(
                value.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            encrypted_data[key] = base64.b64encode(encrypted).decode()
        
        sealed_secret = {
            'apiVersion': 'bitnami.com/v1alpha1',
            'kind': 'SealedSecret',
            'metadata': {
                'name': name,
                'namespace': namespace
            },
            'spec': {
                'encryptedData': encrypted_data
            }
        }
        
        self.sealed_secrets.append(sealed_secret)
        logger.info(f"Sealed secret: {namespace}/{name}")
        return sealed_secret
    
    def unseal_secret(self, sealed_secret: Dict) -> Dict:
        """Unseal a sealed secret (decrypt with private key)"""
        name = sealed_secret['metadata']['name']
        namespace = sealed_secret['metadata']['namespace']
        encrypted_data = sealed_secret['spec']['encryptedData']
        
        # Decrypt each value
        decrypted_data = {}
        for key, encrypted_value in encrypted_data.items():
            encrypted_bytes = base64.b64decode(encrypted_value)
            decrypted = self.private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            decrypted_data[key] = base64.b64encode(decrypted).decode()
        
        # Create Kubernetes Secret
        k8s_secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': name,
                'namespace': namespace,
                'labels': {'managed-by': 'sealed-secrets'}
            },
            'type': 'Opaque',
            'data': decrypted_data
        }
        
        logger.info(f"Unsealed secret: {namespace}/{name}")
        return k8s_secret


def demo_secrets_management():
    """Demonstrate secrets management workflow"""
    print("\n" + "="*60)
    print("EXTERNAL SECRETS OPERATOR DEMO")
    print("="*60)
    
    eso = ExternalSecretsSimulator()
    eso.create_external_secret('db-credentials', 'default', 'prod/db/password')
    eso.create_external_secret('api-key', 'default', 'prod/api/key')
    
    statuses = eso.get_secret_status()
    print("\nExternal Secrets Status:")
    for status in statuses:
        print(json.dumps(asdict(status), indent=2))
    
    print("\n" + "="*60)
    print("SEALED SECRETS DEMO")
    print("="*60)
    
    ss = SealedSecretsSimulator()
    
    print("\nPublic Certificate (for sealing):")
    print(ss.get_public_cert()[:100] + "...")
    
    # Seal a secret
    secret_data = {
        'username': 'admin',
        'password': 'my-super-secret-password'
    }
    
    sealed = ss.seal_secret('default', 'my-app-secret', secret_data)
    print("\nSealed Secret (safe for Git):")
    print(json.dumps(sealed, indent=2)[:300] + "...")
    
    # Unseal it
    unsealed = ss.unseal_secret(sealed)
    print("\nUnsealed Secret (in cluster):")
    # Don't print actual secret values in real systems!
    print(f"Created Kubernetes Secret: {unsealed['metadata']['namespace']}/{unsealed['metadata']['name']}")


if __name__ == '__main__':
    demo_secrets_management()
