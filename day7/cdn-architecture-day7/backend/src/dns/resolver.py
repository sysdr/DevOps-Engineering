import asyncio
import json
from typing import Dict, List
from dataclasses import dataclass
import random
import time

@dataclass
class DNSRecord:
    domain: str
    record_type: str
    value: str
    ttl: int
    priority: int = 10
    weight: int = 100
    health_check_url: str = ""
    status: str = "healthy"

class DNSResolver:
    def __init__(self):
        self.records = self._initialize_records()
        self.health_checks = {}
        
    def _initialize_records(self) -> Dict[str, List[DNSRecord]]:
        return {
            "api.example.com": [
                DNSRecord("api.example.com", "A", "1.2.3.4", 300, 10, 100, "http://1.2.3.4:8080/health"),
                DNSRecord("api.example.com", "A", "5.6.7.8", 300, 20, 50, "http://5.6.7.8:8080/health"),
            ],
            "cdn.example.com": [
                DNSRecord("cdn.example.com", "CNAME", "us-east.edge.example.com", 60),
                DNSRecord("cdn.example.com", "CNAME", "eu-west.edge.example.com", 60),
            ]
        }
        
    async def resolve(self, domain: str, client_ip: str = "127.0.0.1") -> Dict:
        """Resolve domain with geographic and health-based routing"""
        if domain not in self.records:
            return {"error": "Domain not found", "domain": domain}
            
        records = self.records[domain]
        healthy_records = [r for r in records if r.status == "healthy"]
        
        if not healthy_records:
            # Emergency fallback
            healthy_records = records
            
        # Simple geographic routing based on IP (mock)
        if client_ip.startswith("192.168"):
            # Local network - prefer first record
            selected = healthy_records[0]
        else:
            # Weighted random selection
            total_weight = sum(r.weight for r in healthy_records)
            rand = random.randint(1, total_weight)
            current = 0
            selected = healthy_records[0]
            
            for record in healthy_records:
                current += record.weight
                if rand <= current:
                    selected = record
                    break
                    
        return {
            "domain": domain,
            "resolved_to": selected.value,
            "record_type": selected.record_type,
            "ttl": selected.ttl,
            "response_time_ms": random.randint(10, 50)
        }
        
    async def health_check_worker(self):
        """Background health checking"""
        while True:
            for domain, records in self.records.items():
                for record in records:
                    if record.health_check_url:
                        # Simulate health check
                        is_healthy = random.random() > 0.05  # 95% uptime
                        record.status = "healthy" if is_healthy else "failed"
                        
            await asyncio.sleep(30)  # Check every 30 seconds
