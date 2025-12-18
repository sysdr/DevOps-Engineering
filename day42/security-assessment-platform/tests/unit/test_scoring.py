"""Unit tests for scoring engine"""
import sys
sys.path.append('backend')

from services.scoring_engine import calculate_security_score

def test_perfect_score():
    """Test perfect security score"""
    components = {
        "container_security": {"total_score": 100, "max_score": 100},
        "secrets_management": {"total_score": 100, "max_score": 100},
        "runtime_security": {"total_score": 100, "max_score": 100},
        "vulnerability_scanning": {"total_score": 100, "max_score": 100},
        "incident_response": {"total_score": 100, "max_score": 100},
        "supply_chain": {"total_score": 100, "max_score": 100}
    }
    
    result = calculate_security_score(components)
    assert result["total_score"] == 100
    assert result["grade"] == "A"
    assert result["status"] == "excellent"
    print("✅ Perfect score test passed")

def test_weighted_scoring():
    """Test weighted scoring calculation"""
    components = {
        "container_security": {"total_score": 80, "max_score": 100},  # 15% weight
        "secrets_management": {"total_score": 90, "max_score": 100},  # 25% weight
        "runtime_security": {"total_score": 85, "max_score": 100},   # 20% weight
        "vulnerability_scanning": {"total_score": 75, "max_score": 100}, # 20% weight
        "incident_response": {"total_score": 95, "max_score": 100},  # 10% weight
        "supply_chain": {"total_score": 88, "max_score": 100}        # 10% weight
    }
    
    result = calculate_security_score(components)
    # Expected: (80*15 + 90*25 + 85*20 + 75*20 + 95*10 + 88*10) / 100
    # = (1200 + 2250 + 1700 + 1500 + 950 + 880) / 100 = 84.8
    assert 84 <= result["total_score"] <= 85
    assert result["grade"] == "B"
    print("✅ Weighted scoring test passed")

if __name__ == "__main__":
    test_perfect_score()
    test_weighted_scoring()
    print("All scoring tests passed!")
