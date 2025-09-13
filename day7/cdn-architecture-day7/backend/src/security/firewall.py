from typing import Dict, List, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import ipaddress
import hashlib

@dataclass
class SecurityRule:
    name: str
    action: str  # allow, deny, rate_limit
    source_ips: List[str]
    ports: List[int]
    protocols: List[str]
    rate_limit: int = 0  # requests per minute

class NetworkFirewall:
    def __init__(self):
        self.rules = self._default_rules()
        self.rate_limits = {}  # IP -> [timestamps]
        self.blocked_ips = set()
        
    def _default_rules(self) -> List[SecurityRule]:
        return [
            SecurityRule("allow_http", "allow", ["0.0.0.0/0"], [80, 443], ["http", "https"]),
            SecurityRule("rate_limit_api", "rate_limit", ["0.0.0.0/0"], [8080], ["http"], 100),
            SecurityRule("block_suspicious", "deny", ["192.168.100.0/24"], [80, 443, 8080], ["http", "https"])
        ]
        
    def check_request(self, client_ip: str, port: int, protocol: str) -> Dict:
        """Check if request should be allowed"""
        current_time = datetime.now()
        
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            return {"action": "deny", "reason": "IP blocked"}
            
        # Apply rules in order
        for rule in self.rules:
            if self._matches_rule(client_ip, port, protocol, rule):
                if rule.action == "deny":
                    return {"action": "deny", "reason": f"Blocked by rule: {rule.name}"}
                elif rule.action == "rate_limit":
                    if not self._check_rate_limit(client_ip, rule.rate_limit):
                        return {"action": "deny", "reason": "Rate limit exceeded"}
                elif rule.action == "allow":
                    return {"action": "allow", "rule": rule.name}
                    
        return {"action": "deny", "reason": "No matching allow rule"}
        
    def _matches_rule(self, ip: str, port: int, protocol: str, rule: SecurityRule) -> bool:
        """Check if request matches security rule"""
        # Check IP ranges
        ip_match = False
        for rule_ip in rule.source_ips:
            try:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(rule_ip, strict=False):
                    ip_match = True
                    break
            except:
                if ip == rule_ip:
                    ip_match = True
                    break
                    
        # Check ports and protocols
        port_match = port in rule.ports or not rule.ports
        protocol_match = protocol.lower() in [p.lower() for p in rule.protocols] or not rule.protocols
        
        return ip_match and port_match and protocol_match
        
    def _check_rate_limit(self, client_ip: str, limit: int) -> bool:
        """Check rate limiting for IP"""
        current_time = datetime.now()
        minute_ago = current_time - timedelta(minutes=1)
        
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []
            
        # Clean old entries
        self.rate_limits[client_ip] = [
            ts for ts in self.rate_limits[client_ip] if ts > minute_ago
        ]
        
        # Check limit
        if len(self.rate_limits[client_ip]) >= limit:
            return False
            
        # Add current request
        self.rate_limits[client_ip].append(current_time)
        return True
        
    def get_security_stats(self) -> Dict:
        """Get security statistics"""
        current_time = datetime.now()
        minute_ago = current_time - timedelta(minutes=1)
        
        active_connections = {}
        for ip, timestamps in self.rate_limits.items():
            recent = [ts for ts in timestamps if ts > minute_ago]
            if recent:
                active_connections[ip] = len(recent)
                
        return {
            "blocked_ips": list(self.blocked_ips),
            "active_connections": active_connections,
            "security_rules": [
                {"name": rule.name, "action": rule.action, "rate_limit": rule.rate_limit}
                for rule in self.rules
            ],
            "total_ips_tracked": len(self.rate_limits)
        }
