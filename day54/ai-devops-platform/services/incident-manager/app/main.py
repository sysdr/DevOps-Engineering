from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.cluster import DBSCAN
import hashlib

app = FastAPI(title="AI Incident Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Alert(BaseModel):
    id: str
    timestamp: str
    source: str
    severity: str
    message: str
    metadata: Dict = {}

class Incident(BaseModel):
    id: str
    alerts: List[Alert]
    root_cause: Optional[str]
    suggested_resolution: str
    confidence: float
    status: str
    created_at: str

class IncidentManager:
    def __init__(self):
        self.active_alerts: List[Alert] = []
        self.incidents: List[Incident] = []
        self.historical_incidents = self._load_historical_data()
        
    def _load_historical_data(self) -> List[Dict]:
        """Simulate historical incident database"""
        return [
            {
                'symptoms': ['high_cpu', 'memory_pressure', 'slow_response'],
                'root_cause': 'Memory leak in application code',
                'resolution': 'Restart service and apply memory leak fix',
                'success_rate': 0.95
            },
            {
                'symptoms': ['database_timeout', 'connection_pool_exhausted'],
                'root_cause': 'Database connection pool exhaustion',
                'resolution': 'Scale database read replicas',
                'success_rate': 0.90
            },
            {
                'symptoms': ['high_error_rate', 'increased_latency', 'timeout'],
                'root_cause': 'Downstream service degradation',
                'resolution': 'Enable circuit breaker and fallback mechanisms',
                'success_rate': 0.85
            },
            {
                'symptoms': ['disk_full', 'write_failures', 'log_rotation_failed'],
                'root_cause': 'Disk space exhaustion',
                'resolution': 'Clean up old logs and scale storage',
                'success_rate': 1.0
            }
        ]
    
    def ingest_alert(self, alert: Alert) -> Optional[Incident]:
        """Process incoming alert and correlate with existing alerts"""
        self.active_alerts.append(alert)
        
        # Remove old alerts (older than 10 minutes)
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        self.active_alerts = [
            a for a in self.active_alerts
            if datetime.fromisoformat(a.timestamp.replace('Z', '+00:00')) > cutoff
        ]
        
        # If we have enough alerts, try clustering
        if len(self.active_alerts) >= 3:
            return self._correlate_alerts()
        
        return None
    
    def _correlate_alerts(self) -> Optional[Incident]:
        """Use ML to correlate related alerts into incidents"""
        if len(self.active_alerts) < 3:
            return None
        
        # Extract features for clustering
        features = []
        for alert in self.active_alerts:
            feat = self._extract_features(alert)
            features.append(feat)
        
        X = np.array(features)
        
        # Cluster alerts
        clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
        labels = clustering.labels_
        
        # Find largest cluster (excluding noise points labeled -1)
        unique_labels = set(labels)
        unique_labels.discard(-1)
        
        if not unique_labels:
            return None
        
        # Get alerts from largest cluster
        largest_cluster = max(unique_labels, key=lambda x: list(labels).count(x))
        clustered_alerts = [
            alert for alert, label in zip(self.active_alerts, labels)
            if label == largest_cluster
        ]
        
        if len(clustered_alerts) < 2:
            return None
        
        # Sort by timestamp to find temporal patterns
        clustered_alerts.sort(key=lambda x: x.timestamp)
        
        # Analyze root cause
        root_cause = self._identify_root_cause(clustered_alerts)
        suggested_resolution = self._find_resolution(clustered_alerts, root_cause)
        
        # Create incident
        incident_id = hashlib.md5(
            f"{clustered_alerts[0].timestamp}{len(clustered_alerts)}".encode()
        ).hexdigest()[:12]
        
        from datetime import timezone
        incident = Incident(
            id=incident_id,
            alerts=clustered_alerts,
            root_cause=root_cause,
            suggested_resolution=suggested_resolution,
            confidence=0.75 if root_cause else 0.50,
            status="open",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        self.incidents.append(incident)
        return incident
    
    def _extract_features(self, alert: Alert) -> List[float]:
        """Extract numerical features from alert for clustering"""
        features = []
        
        # Severity encoding
        severity_map = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        features.append(severity_map.get(alert.severity.upper(), 2))
        
        # Source encoding (hash to number)
        features.append(hash(alert.source) % 100 / 100.0)
        
        # Message features
        features.append(len(alert.message) / 200.0)
        
        # Keyword presence
        keywords = ['cpu', 'memory', 'disk', 'network', 'database', 'timeout', 'error']
        for keyword in keywords:
            features.append(1.0 if keyword in alert.message.lower() else 0.0)
        
        return features
    
    def _identify_root_cause(self, alerts: List[Alert]) -> Optional[str]:
        """Identify root cause from clustered alerts"""
        # Extract symptoms
        symptoms = set()
        for alert in alerts:
            msg_lower = alert.message.lower()
            if 'cpu' in msg_lower:
                symptoms.add('high_cpu')
            if 'memory' in msg_lower:
                symptoms.add('memory_pressure')
            if 'timeout' in msg_lower:
                symptoms.add('timeout')
            if 'database' in msg_lower:
                symptoms.add('database_timeout')
            if 'disk' in msg_lower:
                symptoms.add('disk_full')
            if 'connection' in msg_lower:
                symptoms.add('connection_pool_exhausted')
            if 'error' in msg_lower:
                symptoms.add('high_error_rate')
            if 'latency' in msg_lower or 'slow' in msg_lower:
                symptoms.add('increased_latency')
        
        # Match against historical incidents
        best_match = None
        best_score = 0
        
        for historical in self.historical_incidents:
            historical_symptoms = set(historical['symptoms'])
            overlap = len(symptoms & historical_symptoms)
            score = overlap / max(len(symptoms), len(historical_symptoms))
            
            if score > best_score:
                best_score = score
                best_match = historical
        
        if best_match and best_score > 0.4:
            return best_match['root_cause']
        
        # Temporal analysis: first alert is likely the cause
        if len(alerts) > 0:
            return f"Triggered by: {alerts[0].source} - {alerts[0].message[:50]}"
        
        return None
    
    def _find_resolution(self, alerts: List[Alert], root_cause: Optional[str]) -> str:
        """Find suggested resolution from historical data"""
        if not root_cause:
            return "Investigate correlated alerts to determine root cause"
        
        # Search historical resolutions
        for historical in self.historical_incidents:
            if historical['root_cause'] == root_cause:
                return f"{historical['resolution']} (Success rate: {historical['success_rate']*100:.0f}%)"
        
        # Generic suggestions based on alert patterns
        alert_count = len(alerts)
        severity_counts = {}
        for alert in alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        
        if severity_counts.get('CRITICAL', 0) > 0:
            return "Immediate escalation required. Check service health and recent deployments."
        elif alert_count > 5:
            return "Multiple related alerts detected. Review system metrics and scale resources if needed."
        else:
            return "Monitor situation. Consider enabling debug logging for affected services."

manager = IncidentManager()

@app.post("/alert", response_model=Optional[Incident])
async def receive_alert(alert: Alert):
    """Receive and process alert, potentially creating incident"""
    incident = manager.ingest_alert(alert)
    return incident

@app.get("/incidents", response_model=List[Incident])
async def get_incidents():
    """Get all active incidents"""
    return manager.incidents

@app.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    """Get specific incident by ID"""
    for incident in manager.incidents:
        if incident.id == incident_id:
            return incident
    raise HTTPException(status_code=404, detail="Incident not found")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "incident-manager"}
