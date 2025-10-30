import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ResourceUsage:
    resource_type: str
    instance_type: str
    hours_used: float
    cpu_utilization: float
    memory_utilization: float
    cost_per_hour: float

@dataclass
class CostRecommendation:
    resource_type: str
    current_cost: float
    recommended_action: str
    potential_savings: float
    impact_level: str

class CostAnalyzer:
    def __init__(self):
        self.resource_costs = self._load_cost_data()
        self.usage_history: List[ResourceUsage] = []
        
    def _load_cost_data(self) -> Dict[str, Dict]:
        """Load cloud provider cost data"""
        return {
            "compute": {
                "t3.micro": {"cpu": 2, "memory": 1, "cost_per_hour": 0.0104},
                "t3.small": {"cpu": 2, "memory": 2, "cost_per_hour": 0.0208},
                "t3.medium": {"cpu": 2, "memory": 4, "cost_per_hour": 0.0416},
                "t3.large": {"cpu": 2, "memory": 8, "cost_per_hour": 0.0832},
                "c5.large": {"cpu": 2, "memory": 4, "cost_per_hour": 0.085},
                "c5.xlarge": {"cpu": 4, "memory": 8, "cost_per_hour": 0.17}
            },
            "database": {
                "db.t3.micro": {"cpu": 2, "memory": 1, "cost_per_hour": 0.017},
                "db.t3.small": {"cpu": 2, "memory": 2, "cost_per_hour": 0.034},
                "db.r5.large": {"cpu": 2, "memory": 16, "cost_per_hour": 0.126}
            },
            "storage": {
                "gp3": {"cost_per_gb_month": 0.08},
                "io2": {"cost_per_gb_month": 0.125}
            },
            "network": {
                "data_transfer_out": {"cost_per_gb": 0.09},
                "nat_gateway": {"cost_per_hour": 0.045}
            }
        }

    def analyze_resource_usage(self, usage_data: List[Dict]) -> Dict[str, Any]:
        """Analyze resource usage patterns for cost optimization"""
        
        # Process usage data
        for data in usage_data:
            usage = ResourceUsage(
                resource_type=data.get("resource_type", "compute"),
                instance_type=data.get("instance_type", "t3.medium"),
                hours_used=data.get("hours_used", 24),
                cpu_utilization=data.get("cpu_utilization", 50),
                memory_utilization=data.get("memory_utilization", 60),
                cost_per_hour=self._get_cost_per_hour(
                    data.get("resource_type", "compute"),
                    data.get("instance_type", "t3.medium")
                )
            )
            self.usage_history.append(usage)
        
        # Generate analysis
        total_cost = self._calculate_total_cost()
        recommendations = self._generate_recommendations()
        utilization_analysis = self._analyze_utilization()
        
        return {
            "current_monthly_cost": total_cost * 30,  # Extrapolate to monthly
            "cost_breakdown": self._generate_cost_breakdown(),
            "utilization_analysis": utilization_analysis,
            "recommendations": [
                {
                    "resource_type": rec.resource_type,
                    "current_cost": rec.current_cost,
                    "recommended_action": rec.recommended_action,
                    "potential_savings": rec.potential_savings,
                    "impact_level": rec.impact_level
                }
                for rec in recommendations
            ],
            "optimization_score": self._calculate_optimization_score()
        }

    def _get_cost_per_hour(self, resource_type: str, instance_type: str) -> float:
        """Get cost per hour for specific resource type and instance"""
        try:
            return self.resource_costs[resource_type][instance_type]["cost_per_hour"]
        except KeyError:
            return 0.05  # Default fallback cost

    def _calculate_total_cost(self) -> float:
        """Calculate total cost from usage history"""
        return sum(usage.hours_used * usage.cost_per_hour for usage in self.usage_history)

    def _generate_cost_breakdown(self) -> Dict[str, float]:
        """Generate cost breakdown by resource type"""
        breakdown = {}
        
        for usage in self.usage_history:
            cost = usage.hours_used * usage.cost_per_hour
            if usage.resource_type in breakdown:
                breakdown[usage.resource_type] += cost
            else:
                breakdown[usage.resource_type] = cost
                
        return breakdown

    def _analyze_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        if not self.usage_history:
            return {"error": "No usage data available"}
        
        cpu_utilization = [usage.cpu_utilization for usage in self.usage_history]
        memory_utilization = [usage.memory_utilization for usage in self.usage_history]
        
        return {
            "average_cpu_utilization": sum(cpu_utilization) / len(cpu_utilization),
            "average_memory_utilization": sum(memory_utilization) / len(memory_utilization),
            "underutilized_resources": self._find_underutilized_resources(),
            "overutilized_resources": self._find_overutilized_resources()
        }

    def _find_underutilized_resources(self) -> List[Dict]:
        """Find resources with low utilization"""
        underutilized = []
        
        for usage in self.usage_history:
            if usage.cpu_utilization < 30 and usage.memory_utilization < 30:
                underutilized.append({
                    "resource_type": usage.resource_type,
                    "instance_type": usage.instance_type,
                    "cpu_utilization": usage.cpu_utilization,
                    "memory_utilization": usage.memory_utilization,
                    "cost_per_hour": usage.cost_per_hour
                })
                
        return underutilized

    def _find_overutilized_resources(self) -> List[Dict]:
        """Find resources with high utilization"""
        overutilized = []
        
        for usage in self.usage_history:
            if usage.cpu_utilization > 80 or usage.memory_utilization > 80:
                overutilized.append({
                    "resource_type": usage.resource_type,
                    "instance_type": usage.instance_type,
                    "cpu_utilization": usage.cpu_utilization,
                    "memory_utilization": usage.memory_utilization,
                    "cost_per_hour": usage.cost_per_hour
                })
                
        return overutilized

    def _generate_recommendations(self) -> List[CostRecommendation]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Analyze each resource for optimization opportunities
        for usage in self.usage_history:
            current_cost = usage.hours_used * usage.cost_per_hour
            
            # Rightsizing recommendations
            if usage.cpu_utilization < 30 and usage.memory_utilization < 30:
                smaller_instance = self._find_smaller_instance(usage.resource_type, usage.instance_type)
                if smaller_instance:
                    potential_savings = current_cost - (usage.hours_used * smaller_instance["cost"])
                    recommendations.append(CostRecommendation(
                        resource_type=usage.resource_type,
                        current_cost=current_cost,
                        recommended_action=f"Downsize from {usage.instance_type} to {smaller_instance['type']}",
                        potential_savings=potential_savings,
                        impact_level="low"
                    ))
            
            # Scaling recommendations
            elif usage.cpu_utilization > 80 or usage.memory_utilization > 80:
                recommendations.append(CostRecommendation(
                    resource_type=usage.resource_type,
                    current_cost=current_cost,
                    recommended_action=f"Scale up {usage.instance_type} or implement auto-scaling",
                    potential_savings=0,  # This prevents performance issues
                    impact_level="high"
                ))
            
            # Reserved instance recommendations
            if usage.hours_used > 20:  # High usage hours
                reserved_savings = current_cost * 0.3  # Typical 30% savings
                recommendations.append(CostRecommendation(
                    resource_type=usage.resource_type,
                    current_cost=current_cost,
                    recommended_action=f"Consider reserved instances for {usage.instance_type}",
                    potential_savings=reserved_savings,
                    impact_level="medium"
                ))
        
        return recommendations

    def _find_smaller_instance(self, resource_type: str, current_instance: str) -> Dict[str, Any]:
        """Find a smaller instance type for downsizing"""
        if resource_type not in self.resource_costs:
            return None
            
        instances = self.resource_costs[resource_type]
        current_cost = instances.get(current_instance, {}).get("cost_per_hour", 0)
        
        # Find smaller instances with lower cost
        for instance_type, specs in instances.items():
            if specs["cost_per_hour"] < current_cost:
                return {"type": instance_type, "cost": specs["cost_per_hour"]}
                
        return None

    def _calculate_optimization_score(self) -> int:
        """Calculate overall cost optimization score (0-100)"""
        if not self.usage_history:
            return 50
        
        # Calculate based on utilization efficiency
        total_cpu_efficiency = sum(min(usage.cpu_utilization, 100) for usage in self.usage_history)
        total_memory_efficiency = sum(min(usage.memory_utilization, 100) for usage in self.usage_history)
        
        avg_efficiency = (total_cpu_efficiency + total_memory_efficiency) / (2 * len(self.usage_history))
        
        # Score based on efficiency (higher utilization = better score)
        if avg_efficiency > 70:
            return min(100, int(avg_efficiency + 15))
        elif avg_efficiency > 50:
            return int(avg_efficiency + 10)
        else:
            return max(20, int(avg_efficiency))

    def generate_cost_report(self) -> str:
        """Generate comprehensive cost analysis report"""
        if not self.usage_history:
            # Generate mock data for demonstration
            mock_usage = [
                {"resource_type": "compute", "instance_type": "t3.medium", "hours_used": 24, "cpu_utilization": 25, "memory_utilization": 30},
                {"resource_type": "compute", "instance_type": "t3.large", "hours_used": 24, "cpu_utilization": 75, "memory_utilization": 80},
                {"resource_type": "database", "instance_type": "db.t3.small", "hours_used": 24, "cpu_utilization": 40, "memory_utilization": 50}
            ]
            analysis = self.analyze_resource_usage(mock_usage)
        else:
            analysis = self.analyze_resource_usage([])
        
        report = f"""
# Cost Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Cost Summary
- **Monthly Cost Estimate**: ${analysis['current_monthly_cost']:.2f}
- **Optimization Score**: {analysis['optimization_score']}/100

## Cost Breakdown
"""
        
        for resource_type, cost in analysis['cost_breakdown'].items():
            report += f"- **{resource_type.title()}**: ${cost:.2f}\n"
        
        report += f"""

## Utilization Analysis
- **Average CPU Utilization**: {analysis['utilization_analysis']['average_cpu_utilization']:.1f}%
- **Average Memory Utilization**: {analysis['utilization_analysis']['average_memory_utilization']:.1f}%

## Optimization Recommendations
"""
        
        for rec in analysis['recommendations']:
            report += f"""
### {rec['resource_type'].title()} Optimization
- **Action**: {rec['recommended_action']}
- **Potential Savings**: ${rec['potential_savings']:.2f}
- **Impact Level**: {rec['impact_level']}
"""
        
        return report
