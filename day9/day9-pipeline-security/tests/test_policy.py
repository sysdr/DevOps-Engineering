"""
Tests for policy validation
"""
import pytest
import asyncio
from src.policy.opa_client import OPAClient

@pytest.mark.asyncio
async def test_validate_policies():
    client = OPAClient()
    result = await client.validate_policies()
    
    assert "total" in result
    assert "passed" in result
    assert "failed" in result
    assert "results" in result

@pytest.mark.asyncio
async def test_create_policy():
    client = OPAClient()
    result = await client.create_policy(
        name="test_policy",
        rule="input.test == true",
        description="Test policy"
    )
    
    assert result["status"] == "created"
    assert "policy" in result
