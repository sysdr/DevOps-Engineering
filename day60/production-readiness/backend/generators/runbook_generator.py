from datetime import datetime
from typing import Dict, List
import hashlib

class RunbookGenerator:
    def __init__(self):
        self.runbooks = {}
        self._initialize_default_runbooks()
    
    def _initialize_default_runbooks(self):
        """Initialize default runbooks"""
        scenarios = [
            "service_degradation",
            "high_latency",
            "memory_leak",
            "database_connection_failure",
            "pod_crash_loop",
            "disk_space_full",
            "certificate_expiration",
            "security_incident",
            "cost_spike",
            "deployment_rollback"
        ]
        
        for scenario in scenarios:
            self.runbooks[scenario] = self._create_runbook(scenario)
    
    def _create_runbook(self, scenario: str) -> Dict:
        """Create a runbook for a scenario"""
        runbook_id = hashlib.md5(scenario.encode()).hexdigest()[:8]
        
        return {
            "id": runbook_id,
            "scenario": scenario,
            "title": scenario.replace("_", " ").title(),
            "created": datetime.utcnow().isoformat(),
            "updated": datetime.utcnow().isoformat(),
            "severity": self._determine_severity(scenario),
            "steps": self._generate_steps(scenario),
            "prerequisites": self._generate_prerequisites(scenario),
            "rollback": self._generate_rollback(scenario),
            "contacts": self._generate_contacts(scenario)
        }
    
    def _determine_severity(self, scenario: str) -> str:
        """Determine severity level"""
        high_severity = ["security_incident", "database_connection_failure", "pod_crash_loop"]
        if scenario in high_severity:
            return "high"
        return "medium"
    
    def _generate_steps(self, scenario: str) -> List[Dict]:
        """Generate resolution steps"""
        return [
            {
                "step": 1,
                "action": f"Identify {scenario.replace('_', ' ')} symptoms",
                "command": "kubectl get pods -A | grep -v Running",
                "expected": "List of non-running pods"
            },
            {
                "step": 2,
                "action": "Check logs for errors",
                "command": f"kubectl logs <pod-name> --tail=100",
                "expected": "Recent log entries"
            },
            {
                "step": 3,
                "action": "Verify resource availability",
                "command": "kubectl top nodes && kubectl top pods",
                "expected": "Resource usage metrics"
            },
            {
                "step": 4,
                "action": "Apply fix or mitigation",
                "command": "kubectl scale deployment <deployment> --replicas=<count>",
                "expected": "Scaling confirmation"
            },
            {
                "step": 5,
                "action": "Verify resolution",
                "command": "kubectl get pods -A",
                "expected": "All pods running"
            }
        ]
    
    def _generate_prerequisites(self, scenario: str) -> List[str]:
        """Generate prerequisites"""
        return [
            "kubectl access to cluster",
            "Appropriate RBAC permissions",
            "Access to monitoring dashboards",
            "Incident response authorization"
        ]
    
    def _generate_rollback(self, scenario: str) -> List[str]:
        """Generate rollback steps"""
        return [
            "Document current state",
            "Create backup if applicable",
            "Revert to previous version",
            "Verify system stability"
        ]
    
    def _generate_contacts(self, scenario: str) -> List[Dict]:
        """Generate contact information"""
        return [
            {"role": "On-call Engineer", "slack": "#oncall"},
            {"role": "SRE Team Lead", "slack": "#sre-team"},
            {"role": "Engineering Manager", "slack": "#engineering"}
        ]
    
    async def generate(self, scenario: str) -> Dict:
        """Generate or retrieve runbook"""
        if scenario in self.runbooks:
            return self.runbooks[scenario]
        
        runbook = self._create_runbook(scenario)
        self.runbooks[scenario] = runbook
        return runbook
    
    async def list_runbooks(self) -> List[Dict]:
        """List all runbooks"""
        return [
            {
                "id": rb["id"],
                "title": rb["title"],
                "scenario": rb["scenario"],
                "severity": rb["severity"],
                "updated": rb["updated"]
            }
            for rb in self.runbooks.values()
        ]
    
    async def get_runbook(self, runbook_id: str) -> Dict:
        """Get specific runbook"""
        for rb in self.runbooks.values():
            if rb["id"] == runbook_id:
                return rb
        return None
    
    async def count(self) -> int:
        """Count runbooks"""
        return len(self.runbooks)
