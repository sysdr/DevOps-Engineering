import asyncio
import uuid
from datetime import datetime
import logging
import random
from typing import List, Dict

from backend.common.models import Incident, IncidentSeverity
from backend.common.metrics import (
    incidents_total, incidents_auto_resolved, mttr
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncidentDetector:
    def __init__(self):
        self.incidents: Dict[str, Incident] = {}
        self.active_incidents = []
        self.remediation_runbooks = {
            'high_error_rate': ['rollback_deployment', 'scale_up', 'alert_oncall'],
            'high_latency': ['scale_up', 'check_dependencies', 'restart_services'],
            'resource_exhaustion': ['scale_up', 'kill_memory_leaks', 'add_nodes'],
            'service_down': ['restart_service', 'failover', 'alert_oncall']
        }
        
    async def start(self):
        """Start incident detection and response"""
        logger.info("Starting autonomous incident detection...")
        asyncio.create_task(self._detection_loop())
        asyncio.create_task(self._response_loop())
    
    async def _detection_loop(self):
        """Continuously monitor for incidents"""
        while True:
            try:
                # Simulate anomaly detection
                metrics = await self._collect_metrics()
                
                # Analyze for anomalies
                incident = await self._analyze_metrics(metrics)
                
                if incident:
                    logger.warning(f"Incident detected: {incident.description}")
                    incidents_total.inc()
                    self.incidents[incident.id] = incident
                    self.active_incidents.append(incident.id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Detection loop error: {e}")
                await asyncio.sleep(10)
    
    async def _response_loop(self):
        """Respond to active incidents"""
        while True:
            try:
                if self.active_incidents:
                    for incident_id in list(self.active_incidents):
                        incident = self.incidents[incident_id]
                        
                        if not incident.resolved_at:
                            await self._remediate_incident(incident)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Response loop error: {e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self) -> dict:
        """Collect system metrics"""
        return {
            'error_rate': random.uniform(0.001, 0.08),
            'latency_p95': random.uniform(100, 500),
            'cpu_utilization': random.uniform(0.3, 0.95),
            'memory_utilization': random.uniform(0.4, 0.9),
            'request_rate': random.uniform(1000, 10000)
        }
    
    async def _analyze_metrics(self, metrics: dict) -> Incident:
        """Analyze metrics for incident patterns"""
        # Simulate incident detection (5% chance)
        if random.random() > 0.95:
            incident_types = [
                ('high_error_rate', IncidentSeverity.HIGH),
                ('high_latency', IncidentSeverity.MEDIUM),
                ('resource_exhaustion', IncidentSeverity.HIGH),
                ('service_down', IncidentSeverity.CRITICAL)
            ]
            
            incident_type, severity = random.choice(incident_types)
            
            return Incident(
                id=str(uuid.uuid4()),
                severity=severity,
                description=f"Detected {incident_type}",
                detected_at=datetime.now(),
                remediation_actions=[]
            )
        
        return None
    
    async def _remediate_incident(self, incident: Incident):
        """Execute automated remediation"""
        start_time = datetime.now()
        logger.info(f"Remediating incident {incident.id}")
        
        try:
            # Get remediation runbook
            incident_type = incident.description.split()[-1]
            actions = self.remediation_runbooks.get(incident_type, ['alert_oncall'])
            
            for action in actions:
                logger.info(f"Executing remediation action: {action}")
                await asyncio.sleep(2)  # Simulate action execution
                incident.remediation_actions.append(action)
                
                # Check if resolved
                if random.random() > 0.3:  # 70% auto-resolution rate
                    incident.resolved_at = datetime.now()
                    incident.auto_resolved = True
                    incidents_auto_resolved.inc()
                    
                    # Record MTTR
                    recovery_duration = (incident.resolved_at - start_time).total_seconds()
                    mttr.observe(recovery_duration)
                    
                    # Remove from active incidents
                    if incident.id in self.active_incidents:
                        self.active_incidents.remove(incident.id)
                    
                    logger.info(f"Incident {incident.id} auto-resolved in {recovery_duration:.2f}s")
                    break
            
            if not incident.resolved_at:
                logger.warning(f"Incident {incident.id} requires manual intervention")
                
        except Exception as e:
            logger.error(f"Remediation failed: {e}")
    
    def get_incident_stats(self) -> dict:
        """Get incident statistics"""
        total = len(self.incidents)
        auto_resolved = sum(1 for i in self.incidents.values() if i.auto_resolved)
        
        return {
            'total_incidents': total,
            'active_incidents': len(self.active_incidents),
            'auto_resolved': auto_resolved,
            'auto_resolution_rate': (auto_resolved / total * 100) if total > 0 else 0,
            'recent_incidents': [
                {
                    'id': i.id,
                    'severity': i.severity,
                    'description': i.description,
                    'auto_resolved': i.auto_resolved,
                    'actions': i.remediation_actions
                }
                for i in list(self.incidents.values())[-10:]
            ]
        }

# Global detector instance
incident_detector = IncidentDetector()
