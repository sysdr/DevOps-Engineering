import requests
import time
import json

API_BASE = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def demo():
    print_section("Model Serving Platform Demo")
    
    # Check health
    print("1. Health Check")
    response = requests.get(f"{API_BASE}/health")
    print(f"   Status: {response.json()['status']}")
    print(f"   Models loaded: {response.json()['models_loaded']}")
    
    # List models
    print_section("2. Available Models")
    response = requests.get(f"{API_BASE}/v1/models")
    for model in response.json()["models"]:
        print(f"   {model['version']}: {model['framework']}, "
              f"{model['size_mb']}MB, {model['accuracy']*100:.1f}% accuracy")
        if model['quantized']:
            print(f"      ✓ Quantized (4x smaller)")
    
    # Current traffic split
    print_section("3. A/B Testing Configuration")
    response = requests.get(f"{API_BASE}/v1/traffic-split")
    split = response.json()
    print(f"   v1: {split['v1']}% of traffic")
    print(f"   v2: {split['v2']}% of traffic")
    
    # Make predictions
    print_section("4. Making Predictions")
    
    test_cases = [
        ([5.1, 3.5, 1.4, 0.2], "Setosa"),
        ([6.5, 3.0, 5.2, 2.0], "Virginica"),
        ([5.9, 3.0, 4.2, 1.5], "Versicolor")
    ]
    
    for features, expected in test_cases:
        response = requests.post(
            f"{API_BASE}/v1/models/predict",
            json={"instances": [features]}
        )
        result = response.json()
        classes = ["Setosa", "Versicolor", "Virginica"]
        predicted = classes[result["predictions"][0]]
        
        print(f"   Input: {features}")
        print(f"   Predicted: {predicted} (expected: {expected})")
        print(f"   Model: {result['model_version']}, Latency: {result['latency_ms']:.2f}ms")
        print()
    
    # Test load
    print_section("5. Load Testing (100 requests)")
    latencies = []
    version_counts = {"v1": 0, "v2": 0, "v2-quantized": 0}
    
    for i in range(100):
        features = [5.5, 3.0, 4.5, 1.5]
        response = requests.post(
            f"{API_BASE}/v1/models/predict",
            json={"instances": [features]}
        )
        result = response.json()
        latencies.append(result["latency_ms"])
        version_counts[result["model_version"]] = version_counts.get(result["model_version"], 0) + 1
    
    print(f"   Average latency: {sum(latencies)/len(latencies):.2f}ms")
    print(f"   Min latency: {min(latencies):.2f}ms")
    print(f"   Max latency: {max(latencies):.2f}ms")
    print(f"\n   Traffic distribution:")
    for version, count in version_counts.items():
        if count > 0:
            print(f"      {version}: {count} requests ({count}%)")
    
    # Compare models
    print_section("6. Model Comparison")
    response = requests.get(f"{API_BASE}/v1/compare-models")
    comparison = response.json()["comparison"]
    
    for version, metrics in comparison.items():
        print(f"   {version}:")
        print(f"      Predictions: {metrics.get('total_predictions', 0)}")
        print(f"      Avg Latency: {metrics.get('avg_latency_ms', 0):.2f}ms")
        print(f"      Accuracy: {metrics['accuracy']*100:.1f}%")
        print(f"      Size: {metrics['size_mb']}MB")
        print()
    
    # Update traffic split
    print_section("7. Updating Traffic Split (Canary Deployment)")
    print("   Increasing v2 traffic to 50%...")
    response = requests.post(
        f"{API_BASE}/v1/traffic-split",
        json={"v1": 50, "v2": 50}
    )
    print(f"   Status: {response.json()['status']}")
    
    new_split = requests.get(f"{API_BASE}/v1/traffic-split").json()
    print(f"   New split: v1={new_split['v1']}%, v2={new_split['v2']}%")
    
    print_section("Demo Complete!")
    print("Dashboard running at: http://localhost:3000")
    print("API running at: http://localhost:8000")
    print("Metrics at: http://localhost:8000/metrics")

if __name__ == "__main__":
    try:
        demo()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Make sure the service is running.")
    except Exception as e:
        print(f"Error: {e}")
