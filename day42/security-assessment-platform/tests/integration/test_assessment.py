"""Integration tests for assessment system"""
import sys
import asyncio
sys.path.append('backend')

from validators.container_security import validate_container_security
from validators.secrets_validator import validate_secrets_management
from services.scoring_engine import calculate_security_score

async def test_full_assessment():
    """Test full assessment workflow"""
    print("Running full assessment integration test...")
    
    # Run validators
    container_results = await validate_container_security()
    secrets_results = await validate_secrets_management()
    
    # Verify results structure
    assert "component" in container_results
    assert "tests" in container_results
    assert "total_score" in container_results
    
    assert "component" in secrets_results
    assert "tests" in secrets_results
    assert "total_score" in secrets_results
    
    # Calculate overall score
    components = {
        "container_security": container_results,
        "secrets_management": secrets_results
    }
    
    score = calculate_security_score(components)
    assert "total_score" in score
    assert "grade" in score
    assert 0 <= score["total_score"] <= 100
    
    print(f"✅ Assessment completed with score: {score['total_score']}")
    print(f"   Grade: {score['grade']}, Status: {score['status']}")

if __name__ == "__main__":
    asyncio.run(test_full_assessment())
    print("Integration tests passed!")
