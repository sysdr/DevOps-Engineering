import pytest
import asyncio
from backend.services.validation_engine import ValidationEngine
from backend.validators.reliability import ReliabilityValidator
from backend.validators.security import SecurityValidator

@pytest.mark.asyncio
async def test_reliability_validator():
    validator = ReliabilityValidator()
    result = await validator.validate()
    
    assert result["pillar"] == "Reliability"
    assert "score" in result
    assert result["score"] >= 0 and result["score"] <= 100
    assert "criteria" in result

@pytest.mark.asyncio
async def test_security_validator():
    validator = SecurityValidator()
    result = await validator.validate()
    
    assert result["pillar"] == "Security"
    assert "score" in result
    assert len(result["criteria"]) > 0

@pytest.mark.asyncio
async def test_validation_engine():
    validators = {
        "reliability": ReliabilityValidator(),
        "security": SecurityValidator()
    }
    
    engine = ValidationEngine(validators)
    result = await engine.run_validation()
    
    assert "overall_score" in result
    assert "scores" in result
    assert "recommendations" in result
    assert len(result["scores"]) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
