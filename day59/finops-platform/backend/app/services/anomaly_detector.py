import random
from datetime import datetime, timedelta
from typing import List, Dict
import math

class AnomalyDetector:
    def __init__(self):
        self.anomalies = []
        self.baseline_costs = {}
        self.alert_threshold = 3.0  # Standard deviations
        
    async def check_anomalies(self):
        """Check for cost anomalies"""
        # Simulate anomaly detection
        if random.random() < 0.1:  # 10% chance of anomaly
            anomaly = {
                "id": f"alert-{datetime.utcnow().timestamp()}",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": random.choice(["warning", "critical"]),
                "namespace": random.choice(["production", "staging", "ml-training"]),
                "baseline_cost": 1250.00,
                "current_cost": 3750.00,
                "deviation_percent": 200.0,
                "reason": "Unusual spike in pod count - scaled from 10 to 120 replicas",
                "acknowledged": False
            }
            self.anomalies.append(anomaly)
            
        # Keep only last 100 anomalies
        self.anomalies = self.anomalies[-100:]
    
    def get_recent_anomalies(self) -> List[Dict]:
        """Get recent unacknowledged anomalies"""
        return [a for a in self.anomalies if not a.get('acknowledged', False)][-10:]
    
    def get_anomaly_history(self, days: int) -> List[Dict]:
        """Get anomaly history"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [a for a in self.anomalies 
                if datetime.fromisoformat(a['timestamp']) > cutoff]
    
    def acknowledge_anomaly(self, alert_id: str):
        """Acknowledge an anomaly"""
        for anomaly in self.anomalies:
            if anomaly['id'] == alert_id:
                anomaly['acknowledged'] = True
                break
