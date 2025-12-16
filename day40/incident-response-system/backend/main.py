from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import random
from datetime import datetime
from typing import List
from threat_detector import ThreatDetector, IncidentResponder, ForensicsCollector
from security_metrics import SecurityMetrics

app = FastAPI(title="Security Operations Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
threat_detector = ThreatDetector()
incident_responder = IncidentResponder()
forensics_collector = ForensicsCollector()
security_metrics = SecurityMetrics()

# Active WebSocket connections
active_connections: List[WebSocket] = []

async def broadcast_event(event: dict):
    """Broadcast event to all connected clients"""
    dead_connections = []
    for connection in active_connections:
        try:
            await connection.send_json(event)
        except:
            dead_connections.append(connection)
    
    for conn in dead_connections:
        active_connections.remove(conn)

def generate_security_event() -> dict:
    """Generate realistic security events for simulation"""
    event_types = [
        {
            'event_type': 'shell_spawn',
            'pod_name': f'webapp-{random.randint(1,5)}',
            'namespace': 'production',
            'command': random.choice(['/bin/bash', '/bin/sh', 'nc -e /bin/bash']),
            'source_ip': random.choice(['192.168.1.10', '192.168.99.100', '10.0.0.5']),
            'cpu_usage': random.randint(20, 95),
            'memory_mb': random.randint(100, 2500),
            'network_connections': random.randint(5, 150)
        },
        {
            'event_type': 'privilege_change',
            'pod_name': f'api-{random.randint(1,3)}',
            'namespace': 'production',
            'command': 'sudo su',
            'new_privilege': random.choice(['user', 'root']),
            'source_ip': '10.0.0.20',
            'cpu_usage': random.randint(10, 40),
            'memory_mb': random.randint(200, 800),
            'network_connections': random.randint(10, 50)
        },
        {
            'event_type': 'network_anomaly',
            'pod_name': f'database-{random.randint(1,2)}',
            'namespace': 'production',
            'command': 'normal',
            'source_ip': '10.0.0.30',
            'external_connection': random.choice([True, False]),
            'network_bytes_out': random.randint(1000, 15000000),
            'cpu_usage': random.randint(30, 98),
            'memory_mb': random.randint(500, 3000),
            'network_connections': random.randint(20, 200)
        },
        {
            'event_type': 'resource_anomaly',
            'pod_name': f'worker-{random.randint(1,4)}',
            'namespace': 'production',
            'command': 'process.py',
            'process_name': random.choice(['python', 'xmrig', 'node']),
            'source_ip': '10.0.0.40',
            'cpu_usage': random.randint(85, 99),
            'memory_mb': random.randint(1000, 4000),
            'network_connections': random.randint(5, 30)
        }
    ]
    
    event = random.choice(event_types)
    event['event_id'] = f"EVT-{int(datetime.utcnow().timestamp())}-{random.randint(1000, 9999)}"
    event['timestamp'] = datetime.utcnow().isoformat()
    
    return event

async def security_event_simulator():
    """Continuously generate and process security events"""
    while True:
        try:
            # Generate event and capture event time
            event_time = datetime.utcnow()
            event = generate_security_event()
            # Update event timestamp to match the captured event_time
            event['timestamp'] = event_time.isoformat()
            
            # Small delay to simulate detection processing time (0.1 to 0.5 seconds)
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Detect threats
            detection_time = datetime.utcnow()
            threat_analysis = threat_detector.analyze_event(event)
            
            # Record detection with event time and detection time
            security_metrics.record_detection(event_time, detection_time, threat_analysis['threat_score'])
            
            # Broadcast threat analysis
            await broadcast_event({
                'type': 'threat_detected',
                'data': threat_analysis
            })
            
            # Execute response if needed
            if threat_analysis['requires_response']:
                response_time = datetime.utcnow()
                incident = await incident_responder.execute_response(threat_analysis)
                
                # Collect forensics
                evidence = await forensics_collector.collect_evidence(incident, threat_analysis)
                
                # Record incident
                security_metrics.record_incident(
                    detection_time,
                    response_time,
                    threat_analysis['severity'],
                    is_true_positive=threat_analysis['threat_score'] > 60
                )
                
                # Broadcast incident
                await broadcast_event({
                    'type': 'incident_response',
                    'data': incident
                })
            
            await asyncio.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"Error in event simulator: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(security_event_simulator())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/api/metrics")
async def get_metrics():
    """Get security metrics summary"""
    return JSONResponse(content=security_metrics.get_metrics_summary())

@app.get("/api/incidents")
async def get_incidents(hours: int = 24):
    """Get recent incidents"""
    incidents = security_metrics.get_recent_incidents(hours)
    return JSONResponse(content={
        'incidents': incidents,
        'count': len(incidents)
    })

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {
            'threat_detector': 'operational',
            'incident_responder': 'operational',
            'forensics_collector': 'operational'
        }
    })

@app.post("/api/test-incident")
async def trigger_test_incident():
    """Manually trigger a test incident"""
    event_time = datetime.utcnow()
    event = {
        'event_id': f"TEST-{int(event_time.timestamp())}",
        'timestamp': event_time.isoformat(),
        'event_type': 'test',
        'pod_name': 'test-pod',
        'namespace': 'testing',
        'command': '/bin/bash',
        'source_ip': '192.168.99.100',
        'cpu_usage': 95,
        'memory_mb': 3000,
        'network_connections': 150,
        'external_connection': True,
        'network_bytes_out': 20000000
    }
    
    # Small delay to simulate detection processing
    await asyncio.sleep(random.uniform(0.1, 0.5))
    detection_time = datetime.utcnow()
    threat_analysis = threat_detector.analyze_event(event)
    
    # Record detection
    security_metrics.record_detection(event_time, detection_time, threat_analysis['threat_score'])
    
    if threat_analysis['requires_response']:
        response_time = datetime.utcnow()
        incident = await incident_responder.execute_response(threat_analysis)
        evidence = await forensics_collector.collect_evidence(incident, threat_analysis)
        
        security_metrics.record_incident(
            detection_time,
            response_time,
            threat_analysis['severity'],
            is_true_positive=True
        )
        
        return JSONResponse(content={
            'status': 'incident_triggered',
            'threat_analysis': threat_analysis,
            'incident': incident,
            'evidence_id': evidence['incident_id']
        })
    
    return JSONResponse(content={
        'status': 'no_response_needed',
        'threat_analysis': threat_analysis
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

