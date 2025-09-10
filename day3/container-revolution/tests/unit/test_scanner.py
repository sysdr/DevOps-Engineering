import pytest
import json
from unittest.mock import Mock, patch
from src.backend.security.scanner import VulnerabilityScanner, SecurityPolicy

class TestVulnerabilityScanner:
    def setup_method(self):
        self.scanner = VulnerabilityScanner()
    
    @patch('subprocess.run')
    def test_update_database_success(self, mock_run):
        mock_run.return_value = Mock(returncode=0)
        result = self.scanner.update_database()
        assert result is True
        assert self.scanner.trivy_db_updated is True
    
    @patch('subprocess.run')
    def test_scan_image_success(self, mock_run):
        mock_result = Mock()
        mock_result.stdout = '{"Results": [{"Vulnerabilities": []}]}'
        mock_run.return_value = mock_result
        
        result = self.scanner.scan_image('test:latest')
        assert result['status'] == 'completed'
        assert 'vulnerabilities' in result

class TestSecurityPolicy:
    def setup_method(self):
        self.policy = SecurityPolicy()
    
    def test_evaluate_no_violations(self):
        scan_results = {
            'vulnerabilities': {'Results': []},
            'secrets': {}
        }
        result = self.policy.evaluate(scan_results)
        assert result['passed'] is True
        assert result['recommendation'] == 'APPROVE'
    
    def test_evaluate_critical_violations(self):
        scan_results = {
            'vulnerabilities': {
                'Results': [{
                    'Vulnerabilities': [{'Severity': 'CRITICAL'}]
                }]
            }
        }
        result = self.policy.evaluate(scan_results)
        assert result['passed'] is False
        assert result['recommendation'] == 'REJECT'
