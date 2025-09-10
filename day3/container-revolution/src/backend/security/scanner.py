import subprocess
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class VulnerabilityScanner:
    def __init__(self):
        self.trivy_db_updated = False
    
    def update_database(self) -> bool:
        """Update Trivy vulnerability database"""
        try:
            subprocess.run(['trivy', 'image', '--download-db-only'], 
                         check=True, capture_output=True)
            self.trivy_db_updated = True
            return True
        except subprocess.CalledProcessError:
            return False
    
    def scan_image(self, image_name: str) -> Dict[str, Any]:
        """Comprehensive image vulnerability scan"""
        if not self.trivy_db_updated:
            self.update_database()
        
        try:
            # Scan for vulnerabilities
            vuln_cmd = ['trivy', 'image', '--format', 'json', 
                       '--severity', 'HIGH,CRITICAL', image_name]
            vuln_result = subprocess.run(vuln_cmd, capture_output=True, text=True)
            
            # Scan for secrets
            secret_cmd = ['trivy', 'image', '--format', 'json', 
                         '--scanners', 'secret', image_name]
            secret_result = subprocess.run(secret_cmd, capture_output=True, text=True)
            
            vulnerabilities = json.loads(vuln_result.stdout) if vuln_result.stdout else {}
            secrets = json.loads(secret_result.stdout) if secret_result.stdout else {}
            
            return {
                'image': image_name,
                'vulnerabilities': vulnerabilities,
                'secrets': secrets,
                'scan_time': self._get_timestamp(),
                'status': 'completed'
            }
        except Exception as e:
            logger.error(f"Scan failed for {image_name}: {e}")
            return {
                'image': image_name,
                'error': str(e),
                'status': 'failed'
            }
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()

class SecurityPolicy:
    def __init__(self):
        self.policies = {
            'max_critical_vulns': 0,
            'max_high_vulns': 5,
            'allow_secrets': False,
            'require_signatures': True
        }
    
    def evaluate(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate scan results against security policies"""
        passed = True
        violations = []
        
        if 'vulnerabilities' in scan_results:
            vulns = scan_results['vulnerabilities']
            critical_count = self._count_severity(vulns, 'CRITICAL')
            high_count = self._count_severity(vulns, 'HIGH')
            
            if critical_count > self.policies['max_critical_vulns']:
                passed = False
                violations.append(f"Critical vulnerabilities: {critical_count}")
            
            if high_count > self.policies['max_high_vulns']:
                passed = False
                violations.append(f"High vulnerabilities: {high_count}")
        
        if 'secrets' in scan_results and scan_results['secrets']:
            if not self.policies['allow_secrets']:
                passed = False
                violations.append("Secrets detected in image")
        
        return {
            'passed': passed,
            'violations': violations,
            'recommendation': 'APPROVE' if passed else 'REJECT'
        }
    
    def _count_severity(self, vulns: Dict, severity: str) -> int:
        count = 0
        if 'Results' in vulns:
            for result in vulns['Results']:
                if 'Vulnerabilities' in result:
                    count += sum(1 for v in result['Vulnerabilities'] 
                               if v.get('Severity') == severity)
        return count
