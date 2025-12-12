from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import hvac
import os
import json
from datetime import datetime, timedelta
import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
import asyncio

app = FastAPI(title="Secrets Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage simulating Vault and Kubernetes secrets
class SecretsStore:
    def __init__(self):
        self.vault_secrets = {}
        self.k8s_secrets = {}
        self.certificates = {}
        self.audit_logs = []
        self.secret_versions = {}
        self.rotation_policies = {}
        self.access_policies = {}
        
    def store_secret(self, path: str, data: Dict, metadata: Dict = None):
        """Store secret with versioning"""
        if path not in self.secret_versions:
            self.secret_versions[path] = []
        
        version = len(self.secret_versions[path]) + 1
        secret_entry = {
            "version": version,
            "data": data,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "encrypted": True
        }
        
        self.secret_versions[path].append(secret_entry)
        self.vault_secrets[path] = secret_entry
        
        self.audit_log("write", path, "success", f"version {version}")
        return version
    
    def get_secret(self, path: str, version: Optional[int] = None):
        """Retrieve secret with optional version"""
        if path not in self.vault_secrets:
            self.audit_log("read", path, "not_found", "")
            return None
        
        if version:
            versions = self.secret_versions.get(path, [])
            if version <= len(versions):
                secret = versions[version - 1]
                self.audit_log("read", path, "success", f"version {version}")
                return secret
            return None
        
        secret = self.vault_secrets[path]
        self.audit_log("read", path, "success", f"version {secret['version']}")
        return secret
    
    def rotate_secret(self, path: str, new_data: Dict):
        """Rotate secret creating new version"""
        return self.store_secret(path, new_data, {"rotated": True})
    
    def audit_log(self, operation: str, path: str, status: str, details: str):
        """Log all secret operations"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "path": path,
            "status": status,
            "details": details,
            "request_id": secrets.token_hex(8)
        }
        self.audit_logs.append(log_entry)
    
    def sync_to_k8s(self, vault_path: str, k8s_namespace: str, k8s_secret_name: str):
        """Sync Vault secret to Kubernetes"""
        vault_secret = self.get_secret(vault_path)
        if vault_secret:
            self.k8s_secrets[f"{k8s_namespace}/{k8s_secret_name}"] = {
                "data": vault_secret["data"],
                "synced_at": datetime.utcnow().isoformat(),
                "source": vault_path,
                "version": vault_secret["version"]
            }
            return True
        return False

secrets_store = SecretsStore()

# Certificate management
class CertificateManager:
    def __init__(self):
        self.certificates = {}
        self.issuers = {
            "letsencrypt": {"type": "acme", "server": "https://acme-v02.api.letsencrypt.org/directory"},
            "vault-pki": {"type": "pki", "server": "http://vault:8200/v1/pki"}
        }
    
    def issue_certificate(self, domain: str, issuer: str = "letsencrypt"):
        """Issue new certificate"""
        cert_id = secrets.token_hex(16)
        
        # Simulate certificate issuance
        cert = {
            "id": cert_id,
            "domain": domain,
            "issuer": issuer,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
            "status": "valid",
            "serial_number": secrets.token_hex(8),
            "auto_renew": True,
            "renewal_threshold_days": 30
        }
        
        self.certificates[domain] = cert
        secrets_store.audit_log("certificate_issue", domain, "success", issuer)
        return cert
    
    def renew_certificate(self, domain: str):
        """Renew existing certificate"""
        if domain in self.certificates:
            old_cert = self.certificates[domain]
            new_cert = self.issue_certificate(domain, old_cert["issuer"])
            secrets_store.audit_log("certificate_renew", domain, "success", f"old_serial: {old_cert['serial_number']}")
            return new_cert
        return None
    
    def check_expiration(self):
        """Check certificates needing renewal"""
        expiring = []
        now = datetime.utcnow()
        
        for domain, cert in self.certificates.items():
            expires = datetime.fromisoformat(cert["expires_at"])
            days_until_expiry = (expires - now).days
            
            if days_until_expiry <= cert["renewal_threshold_days"]:
                expiring.append({
                    "domain": domain,
                    "days_remaining": days_until_expiry,
                    "expires_at": cert["expires_at"]
                })
        
        return expiring

cert_manager = CertificateManager()

# Dynamic secrets generator
class DynamicSecretsEngine:
    def __init__(self):
        self.active_leases = {}
    
    def generate_database_credentials(self, role: str, ttl_hours: int = 24):
        """Generate dynamic database credentials"""
        username = f"db_{role}_{secrets.token_hex(4)}"
        password = secrets.token_urlsafe(32)
        
        lease_id = secrets.token_hex(16)
        lease = {
            "lease_id": lease_id,
            "credentials": {
                "username": username,
                "password": password,
                "host": "postgres.internal",
                "port": 5432,
                "database": "production"
            },
            "ttl": ttl_hours * 3600,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat(),
            "renewable": True,
            "role": role
        }
        
        self.active_leases[lease_id] = lease
        secrets_store.audit_log("dynamic_secret_generate", f"database/{role}", "success", lease_id)
        return lease
    
    def renew_lease(self, lease_id: str, increment_hours: int = 24):
        """Renew a lease"""
        if lease_id in self.active_leases:
            lease = self.active_leases[lease_id]
            new_expires = datetime.utcnow() + timedelta(hours=increment_hours)
            lease["expires_at"] = new_expires.isoformat()
            lease["ttl"] = increment_hours * 3600
            secrets_store.audit_log("lease_renew", lease_id, "success", f"extended by {increment_hours}h")
            return lease
        return None
    
    def revoke_lease(self, lease_id: str):
        """Revoke a lease"""
        if lease_id in self.active_leases:
            lease = self.active_leases.pop(lease_id)
            secrets_store.audit_log("lease_revoke", lease_id, "success", "manual revocation")
            return True
        return False

dynamic_secrets = DynamicSecretsEngine()

# Encryption service
class EncryptionService:
    def __init__(self):
        # Generate master key (in production, this comes from KMS)
        self.master_key = Fernet.generate_key()
        self.cipher = Fernet(self.master_key)
    
    def encrypt_data(self, plaintext: str) -> str:
        """Encrypt data using Fernet"""
        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_data(self, ciphertext: str) -> str:
        """Decrypt data"""
        encrypted = base64.b64decode(ciphertext.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()

encryption_service = EncryptionService()

# Rotation scheduler
class RotationScheduler:
    def __init__(self):
        self.policies = {}
        self.rotation_history = []
    
    def add_policy(self, path: str, interval_hours: int):
        """Add rotation policy"""
        self.policies[path] = {
            "interval_hours": interval_hours,
            "last_rotated": datetime.utcnow().isoformat(),
            "next_rotation": (datetime.utcnow() + timedelta(hours=interval_hours)).isoformat(),
            "enabled": True
        }
    
    def check_rotations_due(self):
        """Check which secrets need rotation"""
        due = []
        now = datetime.utcnow()
        
        for path, policy in self.policies.items():
            next_rotation = datetime.fromisoformat(policy["next_rotation"])
            if now >= next_rotation and policy["enabled"]:
                due.append({
                    "path": path,
                    "policy": policy,
                    "overdue_hours": (now - next_rotation).total_seconds() / 3600
                })
        
        return due
    
    def execute_rotation(self, path: str):
        """Execute secret rotation"""
        # Generate new secret data
        new_data = {
            "password": secrets.token_urlsafe(32),
            "rotated_at": datetime.utcnow().isoformat()
        }
        
        # Rotate in vault
        version = secrets_store.rotate_secret(path, new_data)
        
        # Update policy
        if path in self.policies:
            policy = self.policies[path]
            policy["last_rotated"] = datetime.utcnow().isoformat()
            policy["next_rotation"] = (datetime.utcnow() + timedelta(hours=policy["interval_hours"])).isoformat()
        
        # Record history
        self.rotation_history.append({
            "path": path,
            "timestamp": datetime.utcnow().isoformat(),
            "new_version": version,
            "status": "success"
        })
        
        return version

rotation_scheduler = RotationScheduler()

# Demo data initialization
def seed_demo_data():
    """Initialize demo data for the dashboard"""
    # Add some Vault secrets
    secrets_store.store_secret("database/prod/password", {"password": "encrypted_prod_pass_123"}, {"environment": "production"})
    secrets_store.store_secret("database/staging/password", {"password": "encrypted_staging_pass_456"}, {"environment": "staging"})
    secrets_store.store_secret("api/keys/stripe", {"api_key": "sk_live_abc123xyz789"}, {"service": "stripe"})
    secrets_store.store_secret("api/keys/aws", {"access_key": "AKIAIOSFODNN7EXAMPLE", "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"}, {"service": "aws"})
    secrets_store.store_secret("auth/jwt/secret", {"secret": "super_secret_jwt_key_2024"}, {"type": "jwt"})
    
    # Add certificate with different expiration dates
    cert_manager.issue_certificate("app.example.com", "letsencrypt")
    cert_manager.issue_certificate("api.example.com", "letsencrypt")
    cert_manager.issue_certificate("admin.example.com", "vault-pki")
    
    # Add an expiring certificate (within 30 days)
    expiring_cert = cert_manager.issue_certificate("legacy.example.com", "letsencrypt")
    # Manually set expiration to 15 days from now
    expiring_cert["expires_at"] = (datetime.utcnow() + timedelta(days=15)).isoformat()
    
    # Add another expiring soon (7 days)
    urgent_cert = cert_manager.issue_certificate("critical.example.com", "letsencrypt")
    urgent_cert["expires_at"] = (datetime.utcnow() + timedelta(days=7)).isoformat()
    
    # Generate some dynamic credentials
    dynamic_secrets.generate_database_credentials("readonly", 24)
    dynamic_secrets.generate_database_credentials("readwrite", 48)
    dynamic_secrets.generate_database_credentials("admin", 12)
    
    # Sync some secrets to Kubernetes
    secrets_store.sync_to_k8s("database/prod/password", "production", "db-credentials")
    secrets_store.sync_to_k8s("api/keys/stripe", "production", "stripe-api-key")
    secrets_store.sync_to_k8s("auth/jwt/secret", "default", "jwt-secret")
    
    # Add rotation policies
    rotation_scheduler.add_policy("database/prod/password", 720)  # 30 days
    rotation_scheduler.add_policy("api/keys/stripe", 2160)  # 90 days
    rotation_scheduler.add_policy("auth/jwt/secret", 1440)  # 60 days
    
    # Execute a few rotations for history
    rotation_scheduler.execute_rotation("database/prod/password")
    rotation_scheduler.execute_rotation("api/keys/stripe")

# Seed demo data on startup
@app.on_event("startup")
async def startup_event():
    seed_demo_data()

# API Models
class SecretCreate(BaseModel):
    path: str
    data: Dict
    metadata: Optional[Dict] = None

class SecretRotate(BaseModel):
    path: str

class CertificateRequest(BaseModel):
    domain: str
    issuer: str = "letsencrypt"

class DynamicCredRequest(BaseModel):
    role: str
    ttl_hours: int = 24

class ExternalSecretSync(BaseModel):
    vault_path: str
    k8s_namespace: str
    k8s_secret_name: str

class RotationPolicy(BaseModel):
    path: str
    interval_hours: int

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "Secrets Management System",
        "version": "1.0.0",
        "features": [
            "Vault Integration",
            "Dynamic Secrets",
            "Certificate Management",
            "Secret Rotation",
            "External Secrets Operator",
            "Audit Logging"
        ]
    }

@app.post("/vault/secrets")
async def store_secret(secret: SecretCreate):
    """Store secret in Vault"""
    version = secrets_store.store_secret(secret.path, secret.data, secret.metadata)
    return {
        "status": "success",
        "path": secret.path,
        "version": version,
        "created_at": datetime.utcnow().isoformat()
    }

@app.get("/vault/secrets/{path:path}")
async def get_secret(path: str, version: Optional[int] = None):
    """Retrieve secret from Vault"""
    secret = secrets_store.get_secret(path, version)
    if secret:
        return {
            "status": "success",
            "path": path,
            "data": secret["data"],
            "version": secret["version"],
            "created_at": secret["created_at"]
        }
    raise HTTPException(status_code=404, detail="Secret not found")

@app.post("/vault/secrets/rotate")
async def rotate_secret(request: SecretRotate):
    """Rotate secret"""
    version = rotation_scheduler.execute_rotation(request.path)
    return {
        "status": "success",
        "path": request.path,
        "new_version": version,
        "rotated_at": datetime.utcnow().isoformat()
    }

@app.get("/vault/audit")
async def get_audit_logs(limit: int = 50):
    """Get audit logs"""
    return {
        "total": len(secrets_store.audit_logs),
        "logs": secrets_store.audit_logs[-limit:]
    }

@app.post("/certificates/issue")
async def issue_certificate(request: CertificateRequest):
    """Issue new certificate"""
    cert = cert_manager.issue_certificate(request.domain, request.issuer)
    return {
        "status": "success",
        "certificate": cert
    }

@app.get("/certificates")
async def list_certificates():
    """List all certificates"""
    return {
        "total": len(cert_manager.certificates),
        "certificates": list(cert_manager.certificates.values())
    }

@app.get("/certificates/expiring")
async def check_expiring_certificates():
    """Check certificates needing renewal"""
    expiring = cert_manager.check_expiration()
    return {
        "count": len(expiring),
        "certificates": expiring
    }

@app.post("/certificates/{domain}/renew")
async def renew_certificate(domain: str):
    """Renew certificate"""
    cert = cert_manager.renew_certificate(domain)
    if cert:
        return {
            "status": "success",
            "certificate": cert
        }
    raise HTTPException(status_code=404, detail="Certificate not found")

@app.post("/dynamic/database")
async def generate_database_credentials(request: DynamicCredRequest):
    """Generate dynamic database credentials"""
    lease = dynamic_secrets.generate_database_credentials(request.role, request.ttl_hours)
    return {
        "status": "success",
        "lease": lease
    }

@app.get("/dynamic/leases")
async def list_active_leases():
    """List active leases"""
    return {
        "count": len(dynamic_secrets.active_leases),
        "leases": list(dynamic_secrets.active_leases.values())
    }

@app.post("/dynamic/leases/{lease_id}/renew")
async def renew_lease(lease_id: str, increment_hours: int = 24):
    """Renew a lease"""
    lease = dynamic_secrets.renew_lease(lease_id, increment_hours)
    if lease:
        return {
            "status": "success",
            "lease": lease
        }
    raise HTTPException(status_code=404, detail="Lease not found")

@app.delete("/dynamic/leases/{lease_id}")
async def revoke_lease(lease_id: str):
    """Revoke a lease"""
    success = dynamic_secrets.revoke_lease(lease_id)
    if success:
        return {"status": "success", "message": "Lease revoked"}
    raise HTTPException(status_code=404, detail="Lease not found")

@app.post("/external-secrets/sync")
async def sync_external_secret(request: ExternalSecretSync):
    """Sync Vault secret to Kubernetes"""
    success = secrets_store.sync_to_k8s(
        request.vault_path,
        request.k8s_namespace,
        request.k8s_secret_name
    )
    if success:
        return {
            "status": "success",
            "message": f"Secret synced to {request.k8s_namespace}/{request.k8s_secret_name}"
        }
    raise HTTPException(status_code=404, detail="Vault secret not found")

@app.get("/external-secrets/k8s")
async def list_k8s_secrets():
    """List synced Kubernetes secrets"""
    return {
        "count": len(secrets_store.k8s_secrets),
        "secrets": secrets_store.k8s_secrets
    }

@app.post("/rotation/policies")
async def add_rotation_policy(policy: RotationPolicy):
    """Add rotation policy"""
    rotation_scheduler.add_policy(policy.path, policy.interval_hours)
    return {
        "status": "success",
        "policy": rotation_scheduler.policies[policy.path]
    }

@app.get("/rotation/policies")
async def list_rotation_policies():
    """List rotation policies"""
    return {
        "count": len(rotation_scheduler.policies),
        "policies": rotation_scheduler.policies
    }

@app.get("/rotation/check")
async def check_rotations():
    """Check secrets needing rotation"""
    due = rotation_scheduler.check_rotations_due()
    return {
        "count": len(due),
        "due_for_rotation": due
    }

@app.get("/rotation/history")
async def rotation_history():
    """Get rotation history"""
    return {
        "total": len(rotation_scheduler.rotation_history),
        "history": rotation_scheduler.rotation_history
    }

@app.post("/encryption/encrypt")
async def encrypt_data(data: Dict):
    """Encrypt data"""
    plaintext = json.dumps(data["plaintext"])
    ciphertext = encryption_service.encrypt_data(plaintext)
    return {
        "status": "success",
        "ciphertext": ciphertext
    }

@app.post("/encryption/decrypt")
async def decrypt_data(data: Dict):
    """Decrypt data"""
    plaintext = encryption_service.decrypt_data(data["ciphertext"])
    return {
        "status": "success",
        "plaintext": json.loads(plaintext)
    }

@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    return {
        "vault": {
            "total_secrets": len(secrets_store.vault_secrets),
            "total_versions": sum(len(v) for v in secrets_store.secret_versions.values()),
            "total_audit_logs": len(secrets_store.audit_logs)
        },
        "certificates": {
            "total": len(cert_manager.certificates),
            "expiring_soon": len(cert_manager.check_expiration())
        },
        "dynamic_secrets": {
            "active_leases": len(dynamic_secrets.active_leases)
        },
        "k8s_secrets": {
            "synced": len(secrets_store.k8s_secrets)
        },
        "rotation": {
            "policies": len(rotation_scheduler.policies),
            "total_rotations": len(rotation_scheduler.rotation_history)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
