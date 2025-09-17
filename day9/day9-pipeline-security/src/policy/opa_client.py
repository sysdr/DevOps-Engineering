"""
Open Policy Agent (OPA) client for policy validation
"""
import json
import requests
from typing import Dict, List, Any

class OPAClient:
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
        self.policies = self._load_default_policies()
    
    def _load_default_policies(self) -> List[Dict]:
        """Load default security policies"""
        return [
            {
                "name": "require_non_root_user",
                "description": "Container must not run as root",
                "rule": "input.user != 'root'",
                "severity": "high"
            },
            {
                "name": "require_resource_limits", 
                "description": "Container must have resource limits",
                "rule": "input.resources.limits != null",
                "severity": "medium"
            },
            {
                "name": "disallow_privileged_containers",
                "description": "Privileged containers are not allowed",
                "rule": "input.securityContext.privileged != true",
                "severity": "critical"
            },
            {
                "name": "require_readonly_filesystem",
                "description": "Root filesystem should be read-only",
                "rule": "input.securityContext.readOnlyRootFilesystem == true",
                "severity": "medium"
            }
        ]
    
    async def validate_policies(self, input_data: Dict = None) -> Dict[str, Any]:
        """Validate input against security policies"""
        print("📋 Validating security policies...")
        
        if input_data is None:
            # Default test input
            input_data = {
                "user": "app",
                "resources": {
                    "limits": {"memory": "512Mi", "cpu": "500m"}
                },
                "securityContext": {
                    "privileged": False,
                    "readOnlyRootFilesystem": True,
                    "runAsNonRoot": True
                }
            }
        
        results = []
        passed = 0
        failed = 0
        
        for policy in self.policies:
            # Simulate policy evaluation
            policy_passed = self._evaluate_policy(policy, input_data)
            
            result = {
                "policy": policy["name"],
                "description": policy["description"],
                "passed": policy_passed,
                "severity": policy["severity"]
            }
            
            results.append(result)
            
            if policy_passed:
                passed += 1
            else:
                failed += 1
        
        return {
            "total": len(self.policies),
            "passed": passed,
            "failed": failed,
            "results": results
        }
    
    def _evaluate_policy(self, policy: Dict, input_data: Dict) -> bool:
        """Evaluate a single policy against input data"""
        rule = policy["rule"]
        
        # Simple rule evaluation (in real implementation, use OPA)
        if "input.user != 'root'" in rule:
            return input_data.get("user") != "root"
        elif "input.resources.limits != null" in rule:
            return input_data.get("resources", {}).get("limits") is not None
        elif "input.securityContext.privileged != true" in rule:
            return not input_data.get("securityContext", {}).get("privileged", False)
        elif "input.securityContext.readOnlyRootFilesystem == true" in rule:
            return input_data.get("securityContext", {}).get("readOnlyRootFilesystem", False)
        
        return True
    
    async def create_policy(self, name: str, rule: str, description: str = "") -> Dict[str, Any]:
        """Create a new security policy"""
        policy = {
            "name": name,
            "description": description,
            "rule": rule,
            "severity": "medium"
        }
        
        self.policies.append(policy)
        
        return {"status": "created", "policy": policy}
