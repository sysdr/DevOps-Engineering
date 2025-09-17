"""
Tests for vulnerability scanner
"""
import pytest
import asyncio
from src.scanner.vulnerability_scanner import VulnerabilityScanner

@pytest.mark.asyncio
async def test_scan_image():
    scanner = VulnerabilityScanner()
    result = await scanner.scan_image("node:18-alpine")
    
    assert "critical" in result
    assert "high" in result
    assert "vulnerabilities" in result
    assert isinstance(result["vulnerabilities"], list)

@pytest.mark.asyncio 
async def test_generate_sbom():
    scanner = VulnerabilityScanner()
    result = await scanner.generate_sbom(".")
    
    assert "components" in result
    assert "file" in result
    assert isinstance(result["components"], list)

@pytest.mark.asyncio
async def test_scan_secrets():
    scanner = VulnerabilityScanner()
    result = await scanner.scan_secrets(".")
    
    assert "secrets_found" in result
    assert "files_scanned" in result
    assert isinstance(result["secrets_found"], int)
