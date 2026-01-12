import asyncio
from datetime import datetime
from typing import Dict, List

class ValidationEngine:
    def __init__(self, validators: Dict):
        self.validators = validators
    
    async def run_validation(self) -> Dict:
        """Run all validators"""
        results = {}
        scores = {}
        
        # Run all validators concurrently
        tasks = []
        for name, validator in self.validators.items():
            tasks.append(validator.validate())
        
        validation_results = await asyncio.gather(*tasks)
        
        # Process results
        for result in validation_results:
            pillar = result["pillar"]
            scores[pillar] = result["score"]
            results[pillar] = result
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)
        
        # Determine status
        if overall_score >= 90:
            status = "excellent"
        elif overall_score >= 80:
            status = "good"
        elif overall_score >= 70:
            status = "acceptable"
        else:
            status = "needs_improvement"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": round(overall_score, 2),
            "scores": scores,
            "details": results,
            "status": status,
            "recommendations": self._generate_recommendations(results)
        }
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        for pillar, data in results.items():
            if data["score"] < 80:
                recommendations.append(
                    f"Improve {pillar}: Score is {data['score']:.1f}%, target is 80%+"
                )
            
            # Check specific criteria
            for criterion, details in data.get("criteria", {}).items():
                if details.get("status") == "fail":
                    recommendations.append(
                        f"{pillar} - {criterion}: {details.get('status', 'needs attention')}"
                    )
        
        if not recommendations:
            recommendations.append("All pillars meet production readiness criteria")
        
        return recommendations
