"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ScanRequest(BaseModel):
    target: str
    scan_type: str = "vulnerability"
    options: Optional[Dict[str, Any]] = {}

class VulnerabilityItem(BaseModel):
    id: str
    severity: str
    package: str
    version: str
    description: str

class ScanResult(BaseModel):
    status: str
    vulnerabilities_found: int
    scan_duration: float
    vulnerabilities: List[VulnerabilityItem] = []

class PolicyRule(BaseModel):
    name: str
    description: str
    rule: str
    severity: str

class PolicyResult(BaseModel):
    total: int
    passed: int
    failed: int
    results: List[Dict[str, Any]]

class ComplianceControl(BaseModel):
    control_id: str
    description: str
    status: str
    evidence: str

class ComplianceReport(BaseModel):
    framework: str
    score: int
    total_controls: int
    compliant_controls: int
    controls: List[ComplianceControl]
    timestamp: datetime
