import pytest
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"

def test_api_response_time():
    """Test API response times under normal load"""
    endpoint = f"{BASE_URL}/api/system/metrics"
    response_times = []
    
    for _ in range(50):
        start_time = time.time()
        response = requests.get(endpoint)
        end_time = time.time()
        
        assert response.status_code == 200
        response_times.append(end_time - start_time)
    
    avg_response_time = statistics.mean(response_times)
    p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
    
    print(f"Average response time: {avg_response_time:.3f}s")
    print(f"95th percentile response time: {p95_response_time:.3f}s")
    
    assert avg_response_time < 0.5, f"Average response time too high: {avg_response_time:.3f}s"
    assert p95_response_time < 1.0, f"95th percentile response time too high: {p95_response_time:.3f}s"

def test_concurrent_load():
    """Test API under concurrent load"""
    def make_request():
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/system/metrics")
        end_time = time.time()
        return {
            'status_code': response.status_code,
            'response_time': end_time - start_time
        }
    
    # Test with 20 concurrent users making 100 requests
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [future.result() for future in futures]
    
    # Analyze results
    successful_requests = [r for r in results if r['status_code'] == 200]
    success_rate = len(successful_requests) / len(results)
    
    if successful_requests:
        avg_response_time = statistics.mean([r['response_time'] for r in successful_requests])
        max_response_time = max([r['response_time'] for r in successful_requests])
        
        print(f"Success rate: {success_rate:.2%}")
        print(f"Average response time under load: {avg_response_time:.3f}s")
        print(f"Max response time under load: {max_response_time:.3f}s")
        
        assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"
        assert avg_response_time < 2.0, f"Average response time under load too high: {avg_response_time:.3f}s"

def test_memory_usage():
    """Test that API doesn't have memory leaks"""
    import psutil
    import gc
    
    # Get initial memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Make many requests
    for _ in range(200):
        response = requests.get(f"{BASE_URL}/api/system/metrics")
        assert response.status_code == 200
    
    # Force garbage collection
    gc.collect()
    time.sleep(2)
    
    # Check final memory usage
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    memory_increase_mb = memory_increase / 1024 / 1024
    
    print(f"Memory increase after 200 requests: {memory_increase_mb:.2f}MB")
    
    # Memory increase should be reasonable (less than 50MB)
    assert memory_increase_mb < 50, f"Memory increase too high: {memory_increase_mb:.2f}MB"

if __name__ == "__main__":
    pytest.main([__file__])
