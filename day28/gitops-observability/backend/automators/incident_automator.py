"""Automates incident response based on SLO evaluations"""
from typing import Dict, List, Any
from datetime import datetime

class IncidentAutomator:
    def __init__(self, db):
        self.db = db
        self.status = "healthy"
        self._cooldown: Dict[str, datetime] = {}
    
    async def process(self, evaluations: List[Dict]):
        """Process evaluations and trigger automated responses"""
        try:
            for evaluation in evaluations:
                if evaluation["status"] == "critical":
                    await self._handle_critical(evaluation)
                elif evaluation["status"] == "warning":
                    await self._handle_warning(evaluation)
            
            self.status = "healthy"
        except Exception as e:
            self.status = f"error: {e}"
    
    async def _handle_critical(self, evaluation: Dict):
        slo_id = evaluation["slo_id"]
        
        if self._in_cooldown(slo_id):
            return
        
        incident = {
            "type": "slo_breach",
            "severity": "critical",
            "slo_id": slo_id,
            "slo_name": evaluation["slo_name"],
            "current_value": evaluation["current"],
            "target_value": evaluation["target"],
            "error_budget_remaining": evaluation["error_budget_percent"],
            "actions_taken": await self._execute_runbook(evaluation)
        }
        
        await self.db.add_incident(incident)
        self._set_cooldown(slo_id, minutes=5)
    
    async def _handle_warning(self, evaluation: Dict):
        slo_id = evaluation["slo_id"]
        
        if self._in_cooldown(slo_id):
            return
        
        incident = {
            "type": "slo_warning",
            "severity": "warning",
            "slo_id": slo_id,
            "slo_name": evaluation["slo_name"],
            "current_value": evaluation["current"],
            "target_value": evaluation["target"],
            "error_budget_remaining": evaluation["error_budget_percent"],
            "actions_taken": ["notification_sent"]
        }
        
        await self.db.add_incident(incident)
        self._set_cooldown(slo_id, minutes=10)
    
    async def _execute_runbook(self, evaluation: Dict) -> List[str]:
        actions = []
        
        if evaluation["error_budget_percent"] < 10:
            actions.append("deployments_paused")
            actions.append("oncall_paged")
        
        if evaluation["slo_id"] == "deployment-success-rate":
            actions.append("recent_deployments_analyzed")
        elif evaluation["slo_id"] == "sync-latency-p99":
            actions.append("controller_scaling_triggered")
        
        actions.append("incident_channel_created")
        
        return actions
    
    def _in_cooldown(self, slo_id: str) -> bool:
        if slo_id not in self._cooldown:
            return False
        return datetime.utcnow() < self._cooldown[slo_id]
    
    def _set_cooldown(self, slo_id: str, minutes: int):
        from datetime import timedelta
        self._cooldown[slo_id] = datetime.utcnow() + timedelta(minutes=minutes)
