import asyncio
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
import statistics

class ThreatDetector:
    def __init__(self):
        self.malicious_ips = {
            '192.168.99.100', '10.0.0.50', '172.16.0.100'
        }
        self.suspicious_commands = {
            '/bin/sh', '/bin/bash', 'nc', 'ncat', 'wget', 'curl', 
            'python -c', 'perl -e', 'base64 -d'
        }
        self.baseline_metrics = defaultdict(list)
        self.attack_patterns = self._load_attack_patterns()
        
    def _load_attack_patterns(self) -> Dict[str, List[str]]:
        return {
            'privilege_escalation': [
                'sudo', 'setuid', 'capabilities', 'namespace_escape'
            ],
            'data_exfiltration': [
                'large_network_transfer', 'external_connection', 'file_compression'
            ],
            'lateral_movement': [
                'ssh_connection', 'internal_scan', 'credential_access'
            ],
            'crypto_mining': [
                'high_cpu', 'mining_pool_connection', 'suspicious_process'
            ]
        }
    
    def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        threat_score = 0
        findings = []
        
        # Signature detection (IoCs)
        if event.get('source_ip') in self.malicious_ips:
            threat_score += 40
            findings.append('Known malicious IP detected')
        
        if any(cmd in event.get('command', '') for cmd in self.suspicious_commands):
            threat_score += 35
            findings.append('Suspicious command execution detected')
        
        # Anomaly detection
        anomaly_score = self._detect_anomaly(event)
        threat_score += anomaly_score
        if anomaly_score > 0:
            findings.append(f'Resource anomaly detected (score: {anomaly_score})')
        
        # Behavior detection
        pattern_score = self._detect_attack_pattern(event)
        threat_score += pattern_score
        if pattern_score > 0:
            findings.append(f'Attack pattern matched (score: {pattern_score})')
        
        severity = self._determine_severity(threat_score)
        
        return {
            'event_id': event.get('event_id'),
            'timestamp': datetime.utcnow().isoformat(),
            'threat_score': min(threat_score, 100),
            'severity': severity,
            'findings': findings,
            'requires_response': threat_score >= 50,
            'original_event': event
        }
    
    def _detect_anomaly(self, event: Dict[str, Any]) -> int:
        score = 0
        pod = event.get('pod_name', 'unknown')
        
        # CPU anomaly
        cpu_usage = event.get('cpu_usage', 0)
        self.baseline_metrics[f'{pod}_cpu'].append(cpu_usage)
        
        if len(self.baseline_metrics[f'{pod}_cpu']) > 10:
            recent_values = self.baseline_metrics[f'{pod}_cpu'][-10:]
            mean = statistics.mean(recent_values)
            stdev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0
            
            if stdev > 0 and cpu_usage > mean + 3 * stdev:
                score += 25
        
        # Memory anomaly
        memory_usage = event.get('memory_mb', 0)
        if memory_usage > 2000:  # Suspicious high memory
            score += 15
        
        # Network anomaly
        if event.get('network_connections', 0) > 100:
            score += 20
        
        return score
    
    def _detect_attack_pattern(self, event: Dict[str, Any]) -> int:
        score = 0
        event_type = event.get('event_type', '')
        
        # Privilege escalation pattern
        if event_type == 'privilege_change' and event.get('new_privilege') == 'root':
            score += 30
        
        # Data exfiltration pattern
        if (event.get('network_bytes_out', 0) > 10000000 and 
            event.get('external_connection', False)):
            score += 35
        
        # Crypto mining pattern
        if (event.get('cpu_usage', 0) > 90 and 
            any(proc in event.get('process_name', '') for proc in ['xmrig', 'miner', 'cpuminer'])):
            score += 40
        
        return score
    
    def _determine_severity(self, threat_score: int) -> str:
        if threat_score >= 80:
            return 'CRITICAL'
        elif threat_score >= 60:
            return 'HIGH'
        elif threat_score >= 40:
            return 'MEDIUM'
        elif threat_score >= 20:
            return 'LOW'
        else:
            return 'INFO'

class IncidentResponder:
    def __init__(self):
        self.response_count = 0
        self.playbooks = self._load_playbooks()
    
    def _load_playbooks(self) -> Dict[str, List[str]]:
        return {
            'CRITICAL': [
                'isolate_network',
                'terminate_pod',
                'capture_forensics',
                'alert_security_team',
                'notify_legal'
            ],
            'HIGH': [
                'isolate_network',
                'capture_forensics',
                'alert_security_team',
                'preserve_pod'
            ],
            'MEDIUM': [
                'capture_logs',
                'alert_security_team',
                'monitor_closely'
            ],
            'LOW': [
                'log_event',
                'increment_counter'
            ]
        }
    
    async def execute_response(self, threat_analysis: Dict[str, Any]) -> Dict[str, Any]:
        severity = threat_analysis['severity']
        playbook = self.playbooks.get(severity, [])
        
        actions_executed = []
        for action in playbook:
            result = await self._execute_action(action, threat_analysis)
            actions_executed.append(result)
            await asyncio.sleep(0.1)  # Simulate action execution time
        
        self.response_count += 1
        
        return {
            'incident_id': f"INC-{int(time.time())}-{self.response_count}",
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'threat_score': threat_analysis['threat_score'],
            'actions_executed': actions_executed,
            'response_time_ms': random.randint(200, 800),
            'status': 'completed'
        }
    
    async def _execute_action(self, action: str, threat_analysis: Dict[str, Any]) -> Dict[str, str]:
        action_map = {
            'isolate_network': 'Applied network policy to block all traffic',
            'terminate_pod': 'Terminated pod and blocked image',
            'capture_forensics': 'Captured full forensic evidence package',
            'alert_security_team': 'Sent alert to SOC team via webhook',
            'notify_legal': 'Notified legal team of potential breach',
            'preserve_pod': 'Pod preserved for investigation',
            'capture_logs': 'Captured pod logs and events',
            'monitor_closely': 'Added pod to enhanced monitoring',
            'log_event': 'Event logged to SIEM'
        }
        
        return {
            'action': action,
            'status': 'success',
            'details': action_map.get(action, 'Action executed'),
            'timestamp': datetime.utcnow().isoformat()
        }

class ForensicsCollector:
    def __init__(self):
        import os
        # Use absolute path or relative to project root
        evidence_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'evidence-store')
        self.evidence_store = evidence_path
        # Ensure directory exists
        os.makedirs(self.evidence_store, exist_ok=True)
    
    async def collect_evidence(self, incident: Dict[str, Any], threat_analysis: Dict[str, Any]) -> Dict[str, Any]:
        event = threat_analysis['original_event']
        
        evidence_package = {
            'incident_id': incident['incident_id'],
            'collection_timestamp': datetime.utcnow().isoformat(),
            'pod_snapshot': {
                'pod_name': event.get('pod_name'),
                'namespace': event.get('namespace', 'default'),
                'image': event.get('image'),
                'status': 'terminated' if incident['severity'] == 'CRITICAL' else 'isolated'
            },
            'process_forensics': {
                'command': event.get('command'),
                'pid': event.get('pid', random.randint(1000, 9999)),
                'parent_pid': event.get('parent_pid', random.randint(500, 1000)),
                'user': event.get('user', 'root')
            },
            'network_forensics': {
                'source_ip': event.get('source_ip'),
                'destination_ips': event.get('destination_ips', []),
                'connections': event.get('network_connections', 0),
                'bytes_transferred': event.get('network_bytes_out', 0)
            },
            'resource_forensics': {
                'cpu_usage': event.get('cpu_usage'),
                'memory_mb': event.get('memory_mb'),
                'disk_io': event.get('disk_io', 0)
            },
            'timeline': [
                {
                    'timestamp': threat_analysis['timestamp'],
                    'event': 'Threat detected',
                    'details': ', '.join(threat_analysis['findings'])
                },
                {
                    'timestamp': incident['timestamp'],
                    'event': 'Response executed',
                    'details': f"{len(incident['actions_executed'])} actions completed"
                }
            ],
            'integrity_hash': f"sha256:{random.randint(10**63, 10**64-1):064x}"
        }
        
        # Save evidence
        evidence_file = f"{self.evidence_store}/incident-{incident['incident_id']}.json"
        with open(evidence_file, 'w') as f:
            json.dump(evidence_package, f, indent=2)
        
        return evidence_package

