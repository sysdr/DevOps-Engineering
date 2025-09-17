"""
Tests for compliance monitoring
"""
import pytest
import asyncio
from src.compliance.compliance_monitor import ComplianceMonitor

@pytest.mark.asyncio
async def test_check_compliance():
    monitor = ComplianceMonitor()
    result = await monitor.check_compliance("SOC2")
    
    assert "framework" in result
    assert "score" in result
    assert "controls" in result
    assert result["score"] >= 0 and result["score"] <= 100

@pytest.mark.asyncio
async def test_generate_audit_report():
    monitor = ComplianceMonitor()
    result = await monitor.generate_audit_report("SOC2")
    
    assert "report_id" in result
    assert "framework" in result
    assert "compliance_summary" in result

@pytest.mark.asyncio
async def test_collect_evidence():
    monitor = ComplianceMonitor()
    result = await monitor.collect_evidence()
    
    assert "security_scans" in result
    assert "access_controls" in result
    assert "data_protection" in result
