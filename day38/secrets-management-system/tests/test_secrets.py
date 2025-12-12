import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.mark.asyncio
async def test_store_and_retrieve_secret():
    """Test storing and retrieving secrets"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Store secret
        response = await client.post("/vault/secrets", json={
            "path": "test/password",
            "data": {"password": "secret123"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["version"] == 1
        
        # Retrieve secret
        response = await client.get("/vault/secrets/test/password")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["password"] == "secret123"

@pytest.mark.asyncio
async def test_secret_rotation():
    """Test secret rotation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Store initial secret
        await client.post("/vault/secrets", json={
            "path": "test/rotate",
            "data": {"value": "version1"}
        })
        
        # Rotate secret
        response = await client.post("/vault/secrets/rotate", json={
            "path": "test/rotate"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["new_version"] == 2

@pytest.mark.asyncio
async def test_certificate_issuance():
    """Test certificate issuance"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/certificates/issue", json={
            "domain": "test.example.com",
            "issuer": "letsencrypt"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["certificate"]["domain"] == "test.example.com"
        assert data["certificate"]["status"] == "valid"

@pytest.mark.asyncio
async def test_dynamic_credentials():
    """Test dynamic credentials generation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/dynamic/database", json={
            "role": "readonly",
            "ttl_hours": 24
        })
        assert response.status_code == 200
        data = response.json()
        assert "lease_id" in data["lease"]
        assert "credentials" in data["lease"]
        assert data["lease"]["credentials"]["username"].startswith("db_readonly_")

@pytest.mark.asyncio
async def test_external_secrets_sync():
    """Test external secrets sync to Kubernetes"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Store secret in Vault
        await client.post("/vault/secrets", json={
            "path": "database/prod/creds",
            "data": {"username": "dbuser", "password": "dbpass"}
        })
        
        # Sync to Kubernetes
        response = await client.post("/external-secrets/sync", json={
            "vault_path": "database/prod/creds",
            "k8s_namespace": "production",
            "k8s_secret_name": "db-credentials"
        })
        assert response.status_code == 200
        
        # Verify sync
        response = await client.get("/external-secrets/k8s")
        assert response.status_code == 200
        data = response.json()
        assert "production/db-credentials" in data["secrets"]

@pytest.mark.asyncio
async def test_audit_logging():
    """Test audit logging"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Perform operations
        await client.post("/vault/secrets", json={
            "path": "test/audit",
            "data": {"value": "test"}
        })
        await client.get("/vault/secrets/test/audit")
        
        # Check audit logs
        response = await client.get("/vault/audit")
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) > 0
        assert any(log["operation"] == "write" for log in data["logs"])
        assert any(log["operation"] == "read" for log in data["logs"])

@pytest.mark.asyncio
async def test_statistics():
    """Test statistics endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "vault" in data
        assert "certificates" in data
        assert "dynamic_secrets" in data
