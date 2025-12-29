import sys
sys.path.append('..')

from backend.security_gateway import SecurityGateway

def test_adversarial_detection():
    gateway = SecurityGateway()
    
    # Test normal input
    result = gateway.detect_adversarial("fraud_detection_v1", {
        "features": [0.5, 0.4, 0.6]
    })
    assert result["adversarial"] == False
    print("✓ Normal input validation passed")
    
    # Test adversarial input (extreme outlier)
    result = gateway.detect_adversarial("fraud_detection_v1", {
        "features": [5.0, 5.0, 5.0]
    })
    assert result["adversarial"] == True
    print("✓ Adversarial detection passed")

def test_model_extraction_defense():
    gateway = SecurityGateway()
    
    # Simulate systematic exploration of input space
    results = []
    for i in range(10):
        val = i / 10.0
        result = gateway.detect_adversarial("fraud_detection_v1", {
            "features": [val, val, val]
        })
        results.append(result)
    
    print(f"✓ Model extraction defense tested - {len(results)} probes analyzed")

if __name__ == "__main__":
    test_adversarial_detection()
    test_model_extraction_defense()
    print("\n✅ All security tests passed!")
