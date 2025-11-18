"""Evaluates SLIs against SLO targets and calculates error budgets"""
from typing import Dict, List, Any
from datetime import datetime

class SLOEvaluator:
    def __init__(self, db):
        self.db = db
        self.status = "healthy"
    
    async def evaluate(self, slis: Dict) -> List[Dict]:
        """Evaluate all SLOs against current SLIs"""
        try:
            slo_configs = self.db.get_slo_configs()
            evaluations = []
            
            for slo in slo_configs:
                evaluation = await self._evaluate_slo(slo, slis)
                evaluations.append(evaluation)
                await self.db.update_error_budget(slo["id"], evaluation["error_budget_remaining"])
            
            self.status = "healthy"
            return evaluations
        except Exception as e:
            self.status = f"error: {e}"
            return []
    
    async def _evaluate_slo(self, slo: Dict, slis: Dict) -> Dict:
        indicator = slo["indicator"]
        target = slo["target"]
        
        if indicator == "success_rate":
            current = slis.get("success_rate", {}).get("value", 100)
        elif indicator == "sync_latency_p99":
            threshold = slo.get("threshold_ms", 30000)
            p99_value = slis.get("sync_latency_p99", 0)
            current = 100 if p99_value <= threshold else (threshold / p99_value) * 100
        elif indicator == "reconciliation_success":
            current = slis.get("reconciliation_success", {}).get("value", 100)
        else:
            current = 100
        
        is_meeting = current >= target
        error_budget_total = 100 - target
        error_budget_consumed = max(0, target - current)
        error_budget_remaining = max(0, error_budget_total - error_budget_consumed)
        error_budget_percent = (error_budget_remaining / error_budget_total * 100) if error_budget_total > 0 else 100
        
        status = "healthy"
        if error_budget_percent < 20:
            status = "critical"
        elif error_budget_percent < 50:
            status = "warning"
        
        return {
            "slo_id": slo["id"],
            "slo_name": slo["name"],
            "target": target,
            "current": round(current, 2),
            "is_meeting": is_meeting,
            "error_budget_total": round(error_budget_total, 2),
            "error_budget_consumed": round(error_budget_consumed, 2),
            "error_budget_remaining": round(error_budget_remaining, 2),
            "error_budget_percent": round(error_budget_percent, 2),
            "status": status,
            "evaluated_at": datetime.utcnow().isoformat()
        }
