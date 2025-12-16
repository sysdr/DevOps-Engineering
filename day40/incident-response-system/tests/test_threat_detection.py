import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from threat_detector import ThreatDetector, IncidentResponder, ForensicsCollector
from security_metrics import SecurityMetrics
from datetime import datetime
import asyncio

def test_threat_detector():
    detector = ThreatDetector()
    
    # Test high-severity threat
    event = {
        'event_id': 'TEST-001',
        'pod_name': 'test-pod',
        'command': '/bin/bash',
        'source_ip': '192.168.99.100',
        'cpu_usage': 95,
        'memory_mb': 3000,
        'network_connections': 150
    }
    
    result = detector.analyze_event(event)
    assert result['threat_score'] > 50, "High threat should have score > 50"
    assert result['severity'] in ['HIGH', 'CRITICAL'], f"Expected HIGH/CRITICAL, got {result['severity']}"
    assert len(result['findings']) > 0, "Should have findings"
    print("✓ Threat detection test passed")

def test_anomaly_detection():
    detector = ThreatDetector()
    
    # Establish baseline
    for i in range(15):
        event = {
            'event_id': f'BASELINE-{i}',
            'pod_name': 'test-pod',
            'cpu_usage': 30,
            'memory_mb': 500,
            'network_connections': 20
        }
        detector.analyze_event(event)
    
    # Test anomaly
    anomaly_event = {
        'event_id': 'ANOMALY-001',
        'pod_name': 'test-pod',
        'cpu_usage': 98,
        'memory_mb': 3000,
        'network_connections': 200
    }
    
    result = detector.analyze_event(anomaly_event)
    assert result['threat_score'] > 0, "Anomaly should increase threat score"
    print("✓ Anomaly detection test passed")

async def test_incident_response():
    responder = IncidentResponder()
    
    threat_analysis = {
        'event_id': 'TEST-001',
        'threat_score': 85,
        'severity': 'CRITICAL',
        'findings': ['Test finding'],
        'original_event': {'pod_name': 'test-pod'}
    }
    
    incident = await responder.execute_response(threat_analysis)
    assert 'incident_id' in incident, "Should have incident ID"
    assert len(incident['actions_executed']) > 0, "Should execute actions"
    assert incident['status'] == 'completed', f"Expected completed, got {incident['status']}"
    print("✓ Incident response test passed")

async def test_forensics_collection():
    collector = ForensicsCollector()
    responder = IncidentResponder()
    
    threat_analysis = {
        'event_id': 'TEST-001',
        'timestamp': datetime.utcnow().isoformat(),
        'threat_score': 85,
        'severity': 'HIGH',
        'findings': ['Test finding'],
        'original_event': {
            'pod_name': 'test-pod',
            'command': '/bin/bash',
            'source_ip': '10.0.0.1'
        }
    }
    
    incident = await responder.execute_response(threat_analysis)
    evidence = await collector.collect_evidence(incident, threat_analysis)
    
    assert 'incident_id' in evidence, "Should have incident ID"
    assert 'pod_snapshot' in evidence, "Should have pod snapshot"
    assert 'network_forensics' in evidence, "Should have network forensics"
    assert 'integrity_hash' in evidence, "Should have integrity hash"
    print("✓ Forensics collection test passed")

def test_security_metrics():
    metrics = SecurityMetrics()
    
    detection_time = datetime.utcnow()
    response_time = datetime.utcnow()
    
    metrics.record_incident(detection_time, response_time, 'HIGH', True)
    metrics.record_incident(detection_time, response_time, 'MEDIUM', True)
    metrics.record_incident(detection_time, response_time, 'CRITICAL', False)
    
    summary = metrics.get_metrics_summary()
    assert summary['total_incidents'] == 3, f"Expected 3 incidents, got {summary['total_incidents']}"
    assert summary['true_positives'] == 2, f"Expected 2 true positives, got {summary['true_positives']}"
    assert summary['false_positives'] == 1, f"Expected 1 false positive, got {summary['false_positives']}"
    print("✓ Security metrics test passed")

async def run_async_tests():
    await test_incident_response()
    await test_forensics_collection()

if __name__ == "__main__":
    print("Running Security Operations Center Tests...\n")
    
    test_threat_detector()
    test_anomaly_detection()
    asyncio.run(run_async_tests())
    test_security_metrics()
    
    print("\n✓ All tests passed successfully!")

