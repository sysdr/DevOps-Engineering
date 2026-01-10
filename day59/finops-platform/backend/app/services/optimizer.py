import random
from typing import List, Dict
from datetime import datetime

class CostOptimizer:
    def __init__(self):
        self.recommendations = []
        self.commitment_plans = []
        
    async def generate_recommendations(self) -> List[Dict]:
        """Generate cost optimization recommendations"""
        recommendations = [
            {
                "id": "rec-1",
                "type": "rightsizing",
                "resource": "pod/ml-training-worker",
                "namespace": "ml-training",
                "current_cpu": "4000m",
                "recommended_cpu": "2000m",
                "current_memory": "8Gi",
                "recommended_memory": "4Gi",
                "savings_monthly": 245.50,
                "confidence": 0.92,
                "reason": "Average usage is 25% of requested resources over 14 days"
            },
            {
                "id": "rec-2",
                "type": "commitment",
                "resource": "instance-type/c5.2xlarge",
                "current_spend": 1250.00,
                "commitment_type": "1-year reserved",
                "savings_monthly": 437.50,
                "confidence": 0.88,
                "reason": "Consistent usage pattern suitable for reserved capacity"
            },
            {
                "id": "rec-3",
                "type": "idle_cleanup",
                "resource": "namespace/abandoned-project",
                "namespace": "development",
                "savings_monthly": 180.25,
                "confidence": 0.95,
                "reason": "No traffic received in last 30 days"
            },
            {
                "id": "rec-4",
                "type": "storage_optimization",
                "resource": "pvc/old-logs",
                "namespace": "production",
                "current_size": "500Gi",
                "recommended_size": "100Gi",
                "savings_monthly": 92.00,
                "confidence": 0.85,
                "reason": "Archive to cheaper storage tier"
            }
        ]
        return recommendations
    
    async def analyze_commitments(self):
        """Analyze reserved instance opportunities"""
        # Simulate commitment analysis
        self.commitment_plans = [
            {
                "instance_type": "c5.2xlarge",
                "quantity": 10,
                "term": "1-year",
                "upfront_cost": 15000,
                "monthly_savings": 437.50,
                "payback_months": 2.9
            },
            {
                "instance_type": "m5.large",
                "quantity": 25,
                "term": "3-year",
                "upfront_cost": 42000,
                "monthly_savings": 1250.00,
                "payback_months": 2.8
            }
        ]
    
    async def get_commitment_recommendations(self) -> List[Dict]:
        """Get reserved instance recommendations"""
        return self.commitment_plans
    
    async def get_rightsizing_recommendations(self) -> List[Dict]:
        """Get pod rightsizing recommendations"""
        return [
            {
                "pod": "api-server-xyz",
                "namespace": "production",
                "current_requests": {"cpu": "2000m", "memory": "4Gi"},
                "actual_usage": {"cpu": "450m", "memory": "1.2Gi"},
                "recommended": {"cpu": "600m", "memory": "1.5Gi"},
                "savings": 125.30
            },
            {
                "pod": "worker-batch-abc",
                "namespace": "data-pipeline",
                "current_requests": {"cpu": "4000m", "memory": "8Gi"},
                "actual_usage": {"cpu": "800m", "memory": "2.5Gi"},
                "recommended": {"cpu": "1000m", "memory": "3Gi"},
                "savings": 287.45
            }
        ]
    
    async def find_idle_resources(self) -> List[Dict]:
        """Find idle resources"""
        return [
            {
                "type": "deployment",
                "name": "old-api",
                "namespace": "staging",
                "idle_days": 45,
                "cost_monthly": 156.20
            },
            {
                "type": "statefulset",
                "name": "unused-db",
                "namespace": "development",
                "idle_days": 60,
                "cost_monthly": 420.50
            }
        ]
    
    async def find_oversized_pods(self) -> List[Dict]:
        """Find oversized pods"""
        return [
            {
                "pod": "cache-server",
                "oversize_percentage": 75,
                "waste_cost": 92.50
            }
        ]
    
    async def find_unused_volumes(self) -> List[Dict]:
        """Find unused persistent volumes"""
        return [
            {
                "pvc": "old-data-volume",
                "namespace": "production",
                "size": "100Gi",
                "cost_monthly": 45.00,
                "unused_days": 30
            }
        ]
    
    async def calculate_total_waste(self) -> float:
        """Calculate total waste across all categories"""
        return round(random.uniform(1500, 3000), 2)
