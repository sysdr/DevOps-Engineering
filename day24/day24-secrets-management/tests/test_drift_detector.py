"""
Tests for Drift Detector
"""
import sys
import asyncio
sys.path.append('../backend')

from drift_detector import DriftDetector, ResourceNormalizer


def test_resource_normalization():
    """Test resource normalization"""
    resource = {
        'metadata': {
            'name': 'test',
            'resourceVersion': '12345',
            'generation': 3
        },
        'spec': {'replicas': 3},
        'status': {'ready': True}
    }
    
    normalized = ResourceNormalizer.normalize(resource)
    
    assert 'resourceVersion' not in normalized['metadata']
    assert 'status' not in normalized
    assert normalized['spec']['replicas'] == 3
    print("✓ Resource normalization test passed")


async def test_drift_detection():
    """Test drift detection functionality"""
    detector = DriftDetector()
    await detector.load_git_manifests()
    await detector.fetch_cluster_state()
    
    # Test drift detection
    results = await detector.run_drift_detection()
    
    assert len(results) > 0
    
    # Check that nginx deployment shows drift
    nginx_result = [r for r in results if r.resource_name == 'nginx'][0]
    assert nginx_result.drift_detected == True
    assert 'replicas' in nginx_result.diff_summary
    
    # Check that external secret doesn't show drift
    es_result = [r for r in results if r.resource_name == 'db-credentials'][0]
    assert es_result.drift_detected == False
    
    print("✓ Drift detection test passed")
    
    # Test summary
    summary = detector.get_drift_summary()
    assert summary['total_resources'] == 2
    assert summary['drifted_resources'] == 1
    print("✓ Drift summary test passed")


async def run_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("Running Drift Detector Tests")
    print("="*50 + "\n")
    
    test_resource_normalization()
    await test_drift_detection()
    
    print("\n" + "="*50)
    print("All Drift Detector Tests Passed! ✓")
    print("="*50)


if __name__ == '__main__':
    asyncio.run(run_tests())
