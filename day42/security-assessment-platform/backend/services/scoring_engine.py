"""Security Scoring Engine"""
from typing import Dict

# Scoring weights (total must equal 100)
WEIGHTS = {
    "container_security": 15,
    "secrets_management": 25,
    "runtime_security": 20,
    "vulnerability_scanning": 20,
    "incident_response": 10,
    "supply_chain": 10
}

def calculate_security_score(components: Dict) -> Dict:
    """Calculate weighted security score"""
    component_scores = {}
    weighted_total = 0
    
    for component_name, component_data in components.items():
        if "total_score" in component_data and "max_score" in component_data:
            # Calculate percentage score
            percentage = (component_data["total_score"] / component_data["max_score"]) * 100
            component_scores[component_name] = {
                "score": percentage,
                "raw_score": component_data["total_score"],
                "max_score": component_data["max_score"],
                "weight": WEIGHTS.get(component_name, 0)
            }
            
            # Apply weight
            weighted_score = (percentage * WEIGHTS.get(component_name, 0)) / 100
            weighted_total += weighted_score
    
    # Calculate grade
    if weighted_total >= 90:
        grade = "A"
        status = "excellent"
    elif weighted_total >= 80:
        grade = "B"
        status = "good"
    elif weighted_total >= 70:
        grade = "C"
        status = "acceptable"
    elif weighted_total >= 60:
        grade = "D"
        status = "needs_improvement"
    else:
        grade = "F"
        status = "critical"
    
    return {
        "total_score": round(weighted_total, 2),
        "grade": grade,
        "status": status,
        "component_scores": component_scores,
        "weights": WEIGHTS
    }
