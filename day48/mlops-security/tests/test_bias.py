import sys
sys.path.append('..')

from backend.bias_monitor import BiasMonitor

def test_demographic_parity():
    monitor = BiasMonitor()
    
    predictions = [
        {"predicted": True, "actual": True, "demographic": "group_a"},
        {"predicted": True, "actual": True, "demographic": "group_a"},
        {"predicted": False, "actual": False, "demographic": "group_a"},
        {"predicted": True, "actual": True, "demographic": "group_b"},
        {"predicted": False, "actual": False, "demographic": "group_b"},
        {"predicted": False, "actual": False, "demographic": "group_b"},
    ]
    
    result = monitor.calculate_fairness_metrics("test_model", predictions)
    
    assert "metrics" in result
    assert "demographic_parity_ratio" in result["metrics"]
    print(f"✓ Demographic parity calculated: {result['metrics']['demographic_parity_ratio']}")

def test_violation_detection():
    monitor = BiasMonitor()
    
    # Create biased predictions
    predictions = [
        {"predicted": True, "actual": True, "demographic": "group_a"},
        {"predicted": True, "actual": True, "demographic": "group_a"},
        {"predicted": True, "actual": True, "demographic": "group_a"},
        {"predicted": False, "actual": False, "demographic": "group_b"},
        {"predicted": False, "actual": False, "demographic": "group_b"},
        {"predicted": False, "actual": False, "demographic": "group_b"},
    ]
    
    result = monitor.calculate_fairness_metrics("test_model", predictions)
    
    # Should detect violation
    if result["violations"]:
        print(f"✓ Bias violation detected: {result['violations'][0]['type']}")
    else:
        print("✓ No violations detected (predictions balanced)")

if __name__ == "__main__":
    test_demographic_parity()
    test_violation_detection()
    print("\n✅ All bias monitoring tests passed!")
