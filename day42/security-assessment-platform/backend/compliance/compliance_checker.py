"""Compliance Framework Checker"""
from typing import Dict
from datetime import datetime

SOC2_CONTROLS = {
    "CC6.1": {"name": "Logical Access Controls", "components": ["secrets_management", "container_security"]},
    "CC6.6": {"name": "Vulnerability Management", "components": ["vulnerability_scanning"]},
    "CC6.7": {"name": "Incident Response", "components": ["incident_response", "runtime_security"]},
    "CC7.2": {"name": "System Monitoring", "components": ["runtime_security"]},
}

ISO27001_CONTROLS = {
    "A.12.6.1": {"name": "Vulnerability Management", "components": ["vulnerability_scanning"]},
    "A.14.2.5": {"name": "Secure Development", "components": ["supply_chain"]},
    "A.16.1.5": {"name": "Incident Response", "components": ["incident_response"]},
}

CIS_BENCHMARKS = {
    "5.2.1": {"name": "Pod Security Policies", "components": ["container_security"]},
    "5.3.2": {"name": "Service Account Management", "components": ["secrets_management"]},
    "5.7.1": {"name": "Network Policies", "components": ["runtime_security"]},
}

def generate_compliance_report(components: Dict) -> Dict:
    """Generate compliance report for all frameworks"""
    return {
        "soc2": check_soc2_compliance(components),
        "iso27001": check_iso27001_compliance(components),
        "cis": check_cis_compliance(components)
    }

def check_soc2_compliance(components: Dict) -> Dict:
    """Check SOC 2 compliance"""
    results = {
        "framework": "SOC 2 Type II",
        "assessed_at": datetime.utcnow().isoformat(),
        "controls": []
    }
    
    for control_id, control_info in SOC2_CONTROLS.items():
        control_status = check_control(control_info["components"], components)
        results["controls"].append({
            "id": control_id,
            "name": control_info["name"],
            "status": control_status["status"],
            "score": control_status["score"],
            "evidence": control_status["evidence"]
        })
    
    # Calculate overall compliance
    total_score = sum(c["score"] for c in results["controls"])
    results["compliance_score"] = round(total_score / len(results["controls"]), 2)
    results["status"] = "compliant" if results["compliance_score"] >= 80 else "non_compliant"
    
    return results

def check_iso27001_compliance(components: Dict) -> Dict:
    """Check ISO 27001 compliance"""
    results = {
        "framework": "ISO 27001:2022",
        "assessed_at": datetime.utcnow().isoformat(),
        "controls": []
    }
    
    for control_id, control_info in ISO27001_CONTROLS.items():
        control_status = check_control(control_info["components"], components)
        results["controls"].append({
            "id": control_id,
            "name": control_info["name"],
            "status": control_status["status"],
            "score": control_status["score"],
            "evidence": control_status["evidence"]
        })
    
    total_score = sum(c["score"] for c in results["controls"])
    results["compliance_score"] = round(total_score / len(results["controls"]), 2)
    results["status"] = "compliant" if results["compliance_score"] >= 80 else "non_compliant"
    
    return results

def check_cis_compliance(components: Dict) -> Dict:
    """Check CIS Kubernetes Benchmark compliance"""
    results = {
        "framework": "CIS Kubernetes Benchmark v1.8",
        "assessed_at": datetime.utcnow().isoformat(),
        "controls": []
    }
    
    for control_id, control_info in CIS_BENCHMARKS.items():
        control_status = check_control(control_info["components"], components)
        results["controls"].append({
            "id": control_id,
            "name": control_info["name"],
            "status": control_status["status"],
            "score": control_status["score"],
            "evidence": control_status["evidence"]
        })
    
    total_score = sum(c["score"] for c in results["controls"])
    results["compliance_score"] = round(total_score / len(results["controls"]), 2)
    results["status"] = "compliant" if results["compliance_score"] >= 80 else "non_compliant"
    
    return results

def check_control(component_names: list, components: Dict) -> Dict:
    """Check if control is satisfied by components"""
    total_score = 0
    evidence = []
    
    for comp_name in component_names:
        if comp_name in components:
            comp_data = components[comp_name]
            if "total_score" in comp_data and "max_score" in comp_data:
                score = (comp_data["total_score"] / comp_data["max_score"]) * 100
                total_score += score
                evidence.append(f"{comp_name}: {score:.1f}%")
    
    avg_score = total_score / len(component_names) if component_names else 0
    status = "pass" if avg_score >= 80 else "fail"
    
    return {
        "status": status,
        "score": round(avg_score, 2),
        "evidence": evidence
    }

def generate_framework_report(framework: str, assessment_data: Dict) -> Dict:
    """Generate detailed report for specific framework"""
    components = assessment_data.get("components", {})
    
    if framework == "soc2":
        return check_soc2_compliance(components)
    elif framework == "iso27001":
        return check_iso27001_compliance(components)
    elif framework == "cis":
        return check_cis_compliance(components)
    else:
        return {"error": "Unknown framework"}
