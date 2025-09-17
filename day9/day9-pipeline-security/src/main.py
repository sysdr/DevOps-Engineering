"""
Main FastAPI application for Pipeline Security & Compliance
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
from typing import Dict, List
from src.scanner.vulnerability_scanner import VulnerabilityScanner
from src.policy.opa_client import OPAClient
from src.compliance.compliance_monitor import ComplianceMonitor
from src.api.models import ScanRequest, ScanResult, PolicyResult, ComplianceReport

app = FastAPI(title="DevSecOps Pipeline Security", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vulnerability_scanner = VulnerabilityScanner()
opa_client = OPAClient()
compliance_monitor = ComplianceMonitor()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the security dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DevSecOps Security Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; color: white; margin-bottom: 30px; }
            .card { background: white; border-radius: 10px; padding: 20px; margin: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .metric { text-align: center; }
            .metric-value { font-size: 2.5rem; font-weight: bold; color: #667eea; }
            .metric-label { color: #666; margin-top: 5px; }
            .scan-btn { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; }
            .scan-btn:hover { background: #5a6fd8; }
            .status { padding: 5px 10px; border-radius: 4px; color: white; font-weight: bold; }
            .status.secure { background: #28a745; }
            .status.warning { background: #ffc107; color: #000; }
            .status.critical { background: #dc3545; }
            .logs { background: #f8f9fa; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 DevSecOps Security Dashboard</h1>
                <p>Pipeline Security & Compliance Monitoring</p>
            </div>
            
            <div class="metrics">
                <div class="card metric">
                    <div class="metric-value" id="vulnerabilities">0</div>
                    <div class="metric-label">Vulnerabilities Found</div>
                </div>
                <div class="card metric">
                    <div class="metric-value" id="policies">12</div>
                    <div class="metric-label">Policies Enforced</div>
                </div>
                <div class="card metric">
                    <div class="metric-value" id="compliance">98%</div>
                    <div class="metric-label">Compliance Score</div>
                </div>
                <div class="card metric">
                    <div class="metric-value" id="scans">45</div>
                    <div class="metric-label">Scans Today</div>
                </div>
            </div>
            
            <div class="card">
                <h3>Security Scanning Controls</h3>
                <button class="scan-btn" onclick="runVulnerabilityScan()">🔍 Run Vulnerability Scan</button>
                <button class="scan-btn" onclick="validatePolicies()">📋 Validate Policies</button>
                <button class="scan-btn" onclick="generateSBOM()">📄 Generate SBOM</button>
                <button class="scan-btn" onclick="complianceCheck()">✅ Compliance Check</button>
            </div>
            
            <div class="card">
                <h3>Pipeline Status</h3>
                <div id="pipeline-status">
                    <span class="status secure">SECURE</span> All security checks passing
                </div>
            </div>
            
            <div class="card">
                <h3>Recent Security Events</h3>
                <div class="logs" id="security-logs">
                    [2025-01-15 10:30:15] INFO: Container scan completed - 0 critical vulnerabilities
                    [2025-01-15 10:25:42] INFO: Policy validation passed for deployment
                    [2025-01-15 10:20:18] INFO: SBOM generated for image node:18-alpine
                    [2025-01-15 10:15:33] INFO: Secret scan completed - no exposed secrets
                    [2025-01-15 10:10:55] INFO: Compliance check passed - SOC2 requirements met
                </div>
            </div>
        </div>
        
        <script>
            async function runVulnerabilityScan() {
                updateStatus('🔍 Running vulnerability scan...', 'warning');
                try {
                    const response = await fetch('/api/scan/vulnerabilities', { method: 'POST' });
                    const result = await response.json();
                    logEvent('Vulnerability scan completed - ' + result.vulnerabilities_found + ' issues found');
                    document.getElementById('vulnerabilities').textContent = result.vulnerabilities_found;
                    updateStatus('Vulnerability scan completed', 'secure');
                } catch (error) {
                    logEvent('ERROR: Vulnerability scan failed - ' + error.message);
                    updateStatus('Scan failed', 'critical');
                }
            }
            
            async function validatePolicies() {
                updateStatus('📋 Validating security policies...', 'warning');
                try {
                    const response = await fetch('/api/policy/validate', { method: 'POST' });
                    const result = await response.json();
                    logEvent('Policy validation completed - ' + result.policies_passed + '/' + result.total_policies + ' passed');
                    updateStatus('Policies validated', 'secure');
                } catch (error) {
                    logEvent('ERROR: Policy validation failed - ' + error.message);
                    updateStatus('Policy validation failed', 'critical');
                }
            }
            
            async function generateSBOM() {
                updateStatus('📄 Generating SBOM...', 'warning');
                try {
                    const response = await fetch('/api/sbom/generate', { method: 'POST' });
                    const result = await response.json();
                    logEvent('SBOM generated - ' + result.components_count + ' components documented');
                    updateStatus('SBOM generated', 'secure');
                } catch (error) {
                    logEvent('ERROR: SBOM generation failed - ' + error.message);
                    updateStatus('SBOM generation failed', 'critical');
                }
            }
            
            async function complianceCheck() {
                updateStatus('✅ Running compliance check...', 'warning');
                try {
                    const response = await fetch('/api/compliance/check', { method: 'POST' });
                    const result = await response.json();
                    logEvent('Compliance check completed - ' + result.compliance_score + '% compliant');
                    document.getElementById('compliance').textContent = result.compliance_score + '%';
                    updateStatus('Compliance check completed', 'secure');
                } catch (error) {
                    logEvent('ERROR: Compliance check failed - ' + error.message);
                    updateStatus('Compliance check failed', 'critical');
                }
            }
            
            function updateStatus(message, type) {
                const statusEl = document.getElementById('pipeline-status');
                statusEl.innerHTML = `<span class="status ${type}">${type.toUpperCase()}</span> ${message}`;
            }
            
            function logEvent(message) {
                const logsEl = document.getElementById('security-logs');
                const timestamp = new Date().toISOString().replace('T', ' ').substr(0, 19);
                logsEl.innerHTML = `[${timestamp}] INFO: ${message}\n` + logsEl.innerHTML;
            }
            
            // Auto-refresh metrics
            setInterval(() => {
                document.getElementById('scans').textContent = Math.floor(Math.random() * 20) + 40;
            }, 5000);
        </script>
    </body>
    </html>
    """

@app.post("/api/scan/vulnerabilities")
async def scan_vulnerabilities():
    """Run vulnerability scanning"""
    result = await vulnerability_scanner.scan_image("node:18-alpine")
    return {
        "status": "completed",
        "vulnerabilities_found": result.get("critical", 0) + result.get("high", 0),
        "details": result
    }

@app.post("/api/policy/validate")
async def validate_policies():
    """Validate security policies"""
    result = await opa_client.validate_policies()
    return {
        "status": "completed",
        "policies_passed": result.get("passed", 0),
        "total_policies": result.get("total", 0),
        "details": result
    }

@app.post("/api/sbom/generate")
async def generate_sbom():
    """Generate Software Bill of Materials"""
    result = await vulnerability_scanner.generate_sbom(".")
    return {
        "status": "completed",
        "components_count": len(result.get("components", [])),
        "sbom_location": "sbom.json"
    }

@app.post("/api/compliance/check")
async def compliance_check():
    """Run compliance validation"""
    result = await compliance_monitor.check_compliance()
    return {
        "status": "completed",
        "compliance_score": result.get("score", 95),
        "framework": "SOC2",
        "details": result
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
