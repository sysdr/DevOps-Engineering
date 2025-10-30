import pytest
import asyncio
from src.integration_tests.test_orchestrator import IntegrationTestOrchestrator

@pytest.mark.asyncio
async def test_integration_orchestrator():
    """Test integration test orchestrator functionality"""
    orchestrator = IntegrationTestOrchestrator()
    
    # Test configuration loading
    assert orchestrator.config is not None
    assert "services" in orchestrator.config
    assert "test_scenarios" in orchestrator.config
    
    # Test scenario execution (mock)
    results = await orchestrator.run_integration_tests()
    assert len(results) > 0
    
    # Test report generation
    report = orchestrator.generate_report()
    assert "summary" in report
    assert "results" in report

def test_integration_config():
    """Test integration test configuration"""
    orchestrator = IntegrationTestOrchestrator()
    config = orchestrator.config
    
    assert len(config["services"]) > 0
    assert len(config["test_scenarios"]) > 0
    
    # Validate service configuration structure
    for service_name, service_config in config["services"].items():
        assert "url" in service_config
        assert "health_check" in service_config
