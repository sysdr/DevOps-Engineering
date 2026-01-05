"""
Integration tests for AI DevOps Platform
"""
import requests
import time
import json

BASE_URLS = {
    'code': 'http://localhost:8001',
    'logs': 'http://localhost:8002',
    'incidents': 'http://localhost:8003',
    'docs': 'http://localhost:8004'
}

def test_health_checks():
    """Test health endpoints"""
    print("\n🏥 Testing health endpoints...")
    for service, url in BASE_URLS.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"  ✓ {service.upper()}: Healthy")
            else:
                print(f"  ✗ {service.upper()}: Unhealthy")
        except:
            print(f"  ✗ {service.upper()}: Not responding")

def test_code_analyzer():
    """Test code analyzer"""
    print("\n📝 Testing Code Analyzer...")
    code = """
password = "admin123"
def unsafe_query(user_input):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query
"""
    try:
        response = requests.post(
            f"{BASE_URLS['code']}/analyze",
            json={"code": code, "language": "python", "filename": "test.py"},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Analysis complete: {len(result['issues'])} issues found")
            print(f"  ✓ Code quality score: {result['score']:.1f}/100")
        else:
            print(f"  ✗ Analysis failed: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

def test_log_analyzer():
    """Test log analyzer"""
    print("\n📊 Testing Log Analyzer...")
    log_entry = {
        "timestamp": "2024-01-15T10:30:00Z",
        "level": "ERROR",
        "message": "Database connection timeout",
        "source": "api-server",
        "metadata": {}
    }
    try:
        response = requests.post(
            f"{BASE_URLS['logs']}/ingest",
            json=log_entry,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Log ingested successfully")
            print(f"  ✓ Anomaly detected: {result['is_anomaly']}")
        else:
            print(f"  ✗ Log ingestion failed: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

def test_incident_manager():
    """Test incident manager"""
    print("\n🚨 Testing Incident Manager...")
    alert = {
        "id": "test-123",
        "timestamp": "2024-01-15T10:30:00Z",
        "source": "database",
        "severity": "HIGH",
        "message": "High CPU usage detected: 95%",
        "metadata": {}
    }
    try:
        response = requests.post(
            f"{BASE_URLS['incidents']}/alert",
            json=alert,
            timeout=10
        )
        if response.status_code == 200:
            print(f"  ✓ Alert processed successfully")
        else:
            print(f"  ✗ Alert processing failed: {response.status_code}")
        
        # Get incidents
        response = requests.get(f"{BASE_URLS['incidents']}/incidents", timeout=10)
        if response.status_code == 200:
            incidents = response.json()
            print(f"  ✓ Retrieved {len(incidents)} incidents")
        else:
            print(f"  ✗ Failed to retrieve incidents")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

def test_doc_generator():
    """Test documentation generator"""
    print("\n📚 Testing Documentation Generator...")
    code_file = {
        "filename": "test.py",
        "content": '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers"""
    return a + b

class Calculator:
    """Simple calculator class"""
    def add(self, x, y):
        return x + y
''',
        "language": "python"
    }
    try:
        response = requests.post(
            f"{BASE_URLS['docs']}/generate",
            json=code_file,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Documentation generated")
            print(f"  ✓ Found {len(result['sections'])} sections")
        else:
            print(f"  ✗ Doc generation failed: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

if __name__ == '__main__':
    print("=" * 50)
    print("AI DevOps Platform - Integration Tests")
    print("=" * 50)
    
    test_health_checks()
    test_code_analyzer()
    test_log_analyzer()
    test_incident_manager()
    test_doc_generator()
    
    print("\n" + "=" * 50)
    print("✅ Testing complete!")
    print("=" * 50)
