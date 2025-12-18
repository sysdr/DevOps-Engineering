"""Incident Response Playbook Generator"""
from typing import Dict, List
from datetime import datetime

PLAYBOOK_TEMPLATES = {
    "container_escape": {
        "title": "Container Escape Incident Response",
        "severity": "critical",
        "steps": [
            "Immediately isolate affected pod using NetworkPolicy",
            "Capture forensic data: kubectl logs <pod> --previous",
            "Review runtime security alerts from Falco",
            "Identify attack vector and patch vulnerability",
            "Scan cluster for similar compromised pods",
            "Update Pod Security Standards to prevent recurrence",
            "Document incident and update playbook"
        ]
    },
    "secret_exposure": {
        "title": "Secret Exposure Incident Response",
        "severity": "critical",
        "steps": [
            "Immediately rotate exposed secrets in Vault",
            "Audit secret access logs for unauthorized use",
            "Identify exposure vector (logs, env vars, etc.)",
            "Scan codebase and configs for other exposures",
            "Update access controls and encryption",
            "Notify affected services of rotation",
            "Implement secret scanning in CI/CD"
        ]
    },
    "cve_critical": {
        "title": "Critical CVE Remediation",
        "severity": "high",
        "steps": [
            "Identify all affected images and deployments",
            "Check if CVE is actively exploited (CISA KEV)",
            "Build patched images with updated dependencies",
            "Test patched images in staging environment",
            "Schedule maintenance window for production",
            "Deploy patched images with rolling update",
            "Verify vulnerability resolved with Trivy scan"
        ]
    },
    "privilege_escalation": {
        "title": "Privilege Escalation Response",
        "severity": "critical",
        "steps": [
            "Revoke elevated privileges immediately",
            "Review RBAC policies for over-permissive roles",
            "Audit recent API server requests for abuse",
            "Identify compromised service account",
            "Rotate service account tokens",
            "Implement least-privilege principle",
            "Add monitoring for privilege escalation attempts"
        ]
    },
    "supply_chain_compromise": {
        "title": "Supply Chain Compromise Response",
        "severity": "critical",
        "steps": [
            "Quarantine suspected compromised images",
            "Review SBOM for malicious dependencies",
            "Verify image signatures and provenance",
            "Scan for backdoors and malicious code",
            "Identify trust boundary breach point",
            "Rebuild images from trusted sources",
            "Implement stricter supply chain controls"
        ]
    }
}

def generate_playbook(vulnerability_type: str) -> Dict:
    """Generate incident response playbook"""
    if vulnerability_type not in PLAYBOOK_TEMPLATES:
        return {"error": "Unknown vulnerability type"}
    
    template = PLAYBOOK_TEMPLATES[vulnerability_type]
    
    return {
        "playbook_id": f"{vulnerability_type}-{datetime.utcnow().timestamp()}",
        "title": template["title"],
        "severity": template["severity"],
        "generated_at": datetime.utcnow().isoformat(),
        "steps": template["steps"],
        "automation": {
            "available": True,
            "automated_steps": ["Isolation", "Log capture", "Alert routing"],
            "manual_steps": ["Root cause analysis", "Documentation"]
        }
    }

def get_all_playbooks() -> List[Dict]:
    """Get list of all available playbooks"""
    return [
        {
            "type": vuln_type,
            "title": template["title"],
            "severity": template["severity"]
        }
        for vuln_type, template in PLAYBOOK_TEMPLATES.items()
    ]
