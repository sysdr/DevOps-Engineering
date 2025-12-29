from typing import Dict, Any, List

class BiasMonitor:
    def __init__(self):
        self.fairness_thresholds = {
            "demographic_parity_ratio": 0.8,
            "equal_opportunity_diff": 0.1
        }
        self.analyses = {}
    
    def calculate_fairness_metrics(self, model_id: str, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate fairness metrics across demographics"""
        
        # Group predictions by demographic
        groups = {}
        for pred in predictions:
            demo = pred.get("demographic", "unknown")
            if demo not in groups:
                groups[demo] = []
            groups[demo].append(pred)
        
        metrics = {}
        
        # Calculate demographic parity
        positive_rates = {}
        for group_name, group_preds in groups.items():
            positive_count = sum(1 for p in group_preds if p.get("predicted"))
            positive_rate = positive_count / len(group_preds) if group_preds else 0
            positive_rates[group_name] = positive_rate
            metrics[f"positive_rate_{group_name}"] = round(positive_rate, 3)
        
        # Calculate parity ratio
        if positive_rates:
            max_rate = max(positive_rates.values())
            min_rate = min(positive_rates.values())
            parity_ratio = min_rate / max_rate if max_rate > 0 else 1.0
            metrics["demographic_parity_ratio"] = round(parity_ratio, 3)
        
        # Calculate equal opportunity (TPR)
        tpr_by_group = {}
        for group_name, group_preds in groups.items():
            true_positives = sum(1 for p in group_preds if p.get("predicted") and p.get("actual"))
            actual_positives = sum(1 for p in group_preds if p.get("actual"))
            tpr = true_positives / actual_positives if actual_positives > 0 else 0
            tpr_by_group[group_name] = tpr
            metrics[f"tpr_{group_name}"] = round(tpr, 3)
        
        # Check for violations
        violations = []
        if metrics.get("demographic_parity_ratio", 1.0) < self.fairness_thresholds["demographic_parity_ratio"]:
            violations.append({
                "type": "demographic_parity",
                "threshold": self.fairness_thresholds["demographic_parity_ratio"],
                "actual": metrics["demographic_parity_ratio"]
            })
        
        # Store analysis
        self.analyses[model_id] = {
            "metrics": metrics,
            "violations": violations,
            "timestamp": None
        }
        
        return {
            "metrics": metrics,
            "violations": violations,
            "groups_analyzed": list(groups.keys())
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bias monitoring statistics"""
        total_violations = sum(len(a["violations"]) for a in self.analyses.values())
        
        return {
            "models_analyzed": len(self.analyses),
            "total_violations": total_violations
        }
