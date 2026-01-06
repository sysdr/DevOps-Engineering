import pytest
import requests
import time

BASE_URL_BIAS = "http://localhost:8001"
BASE_URL_FAIRNESS = "http://localhost:8002"
BASE_URL_EXPLAIN = "http://localhost:8003"
BASE_URL_GOVERNANCE = "http://localhost:8004"

def test_bias_detection():
    """Test bias detection API"""
    response = requests.post(
        f"{BASE_URL_BIAS}/api/v1/bias/analyze",
        json={
            "model_id": "test-model-1",
            "dataset_id": "test-dataset-1"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "demographic_parity" in data
    assert "passed" in data
    print(f"✓ Bias Detection Test Passed - Parity: {data['demographic_parity']:.3f}")

def test_fairness_monitoring():
    """Test fairness monitoring API"""
    # Log some predictions
    for i in range(10):
        requests.post(
            f"{BASE_URL_FAIRNESS}/api/v1/monitor/log",
            json={
                "model_id": "test-model-1",
                "prediction": 0.5 + (i % 2) * 0.1,
                "group": f"Group_{i % 3}"
            }
        )
    
    # Get metrics
    response = requests.get(f"{BASE_URL_FAIRNESS}/api/v1/monitor/metrics/test-model-1")
    assert response.status_code == 200
    data = response.json()
    assert "fairness_ratio" in data
    print(f"✓ Fairness Monitoring Test Passed - Ratio: {data['fairness_ratio']:.3f}")

def test_explainability():
    """Test explainability API"""
    import time
    prediction_id = f"pred-test-{int(time.time() * 1000)}"
    response = requests.post(
        f"{BASE_URL_EXPLAIN}/api/v1/explain/generate",
        json={
            "model_id": "test-model-1",
            "prediction_id": prediction_id,
            "input_data": {
                "credit_score": 650,
                "income": 60000,
                "debt_ratio": 0.35,
                "age": 30
            },
            "prediction": 0.65
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "shap_values" in data
    assert "natural_language" in data
    print(f"✓ Explainability Test Passed - Generated explanation")

def test_governance_workflow():
    """Test governance workflow API"""
    import time
    model_id = f"workflow-test-{int(time.time() * 1000)}"
    # Submit model
    response = requests.post(
        f"{BASE_URL_GOVERNANCE}/api/v1/governance/submit",
        json={
            "model_id": model_id,
            "owner": "test@example.com"
        }
    )
    assert response.status_code == 200
    
    # Update bias result
    time.sleep(1)
    response = requests.post(
        f"{BASE_URL_GOVERNANCE}/api/v1/governance/bias-result",
        params={"model_id": model_id, "passed": True}
    )
    assert response.status_code == 200
    
    # Get status
    response = requests.get(f"{BASE_URL_GOVERNANCE}/api/v1/governance/status/{model_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["current_state"] in ["peer_review_pending", "bias_analysis_passed"]
    print(f"✓ Governance Workflow Test Passed - State: {data['current_state']}")

if __name__ == "__main__":
    print("Running Integration Tests...")
    print("=" * 50)
    
    try:
        test_bias_detection()
        test_fairness_monitoring()
        test_explainability()
        test_governance_workflow()
        print("=" * 50)
        print("✓ All Integration Tests Passed!")
    except Exception as e:
        print(f"✗ Test Failed: {e}")
        raise
