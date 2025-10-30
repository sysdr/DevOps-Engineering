import pytest
from src.cost_analysis.cost_analyzer import CostAnalyzer

def test_cost_analyzer():
    """Test cost analysis functionality"""
    analyzer = CostAnalyzer()
    
    # Test cost data loading
    assert "compute" in analyzer.resource_costs
    assert "database" in analyzer.resource_costs
    
    # Test analysis with mock data
    mock_usage = [
        {
            "resource_type": "compute",
            "instance_type": "t3.medium",
            "hours_used": 24,
            "cpu_utilization": 30,
            "memory_utilization": 40
        }
    ]
    
    analysis = analyzer.analyze_resource_usage(mock_usage)
    assert "current_monthly_cost" in analysis
    assert "recommendations" in analysis
    assert "optimization_score" in analysis

def test_cost_recommendations():
    """Test cost optimization recommendations"""
    analyzer = CostAnalyzer()
    
    # Test underutilized resource detection
    underutilized = analyzer._find_underutilized_resources()
    assert isinstance(underutilized, list)
    
    # Test optimization score calculation
    score = analyzer._calculate_optimization_score()
    assert 0 <= score <= 100
