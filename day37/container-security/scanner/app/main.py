from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import asyncio
import json
import sqlite3
import subprocess
import os
import hashlib

app = FastAPI(title="Container Security Scanner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_db():
    conn = sqlite3.connect('scanner.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  image TEXT NOT NULL,
                  image_digest TEXT,
                  scan_time TEXT NOT NULL,
                  status TEXT NOT NULL,
                  critical INTEGER DEFAULT 0,
                  high INTEGER DEFAULT 0,
                  medium INTEGER DEFAULT 0,
                  low INTEGER DEFAULT 0,
                  results TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS policies
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  severity_threshold TEXT NOT NULL,
                  action TEXT NOT NULL,
                  active INTEGER DEFAULT 1)''')
    # Insert default policy
    c.execute('''INSERT OR IGNORE INTO policies (name, severity_threshold, action, active)
                 VALUES ('default', 'CRITICAL', 'block', 1)''')
    conn.commit()
    conn.close()

init_db()

class ScanRequest(BaseModel):
    image: str
    policy: Optional[str] = "default"

class ScanResponse(BaseModel):
    scan_id: int
    image: str
    status: str
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    blocked: bool = False
    message: str = ""

class PolicyModel(BaseModel):
    name: str
    severity_threshold: str
    action: str
    active: bool = True

# Simulated Trivy scanning (in production, this would call actual Trivy)
async def simulate_trivy_scan(image: str) -> Dict:
    """Simulate vulnerability scanning with realistic CVE data"""
    await asyncio.sleep(2)  # Simulate scan time
    
    # Simulate different vulnerability profiles based on image
    if "vulnerable" in image.lower() or "old" in image.lower():
        return {
            "critical": 3,
            "high": 7,
            "medium": 12,
            "low": 8,
            "vulnerabilities": [
                {
                    "cve": "CVE-2021-44228",
                    "severity": "CRITICAL",
                    "package": "log4j-core",
                    "version": "2.14.1",
                    "fixed_version": "2.17.1",
                    "description": "Log4Shell RCE vulnerability"
                },
                {
                    "cve": "CVE-2022-0778",
                    "severity": "HIGH",
                    "package": "openssl",
                    "version": "1.1.1k",
                    "fixed_version": "1.1.1n",
                    "description": "Infinite loop in BN_mod_sqrt()"
                }
            ]
        }
    elif "nginx" in image.lower():
        return {
            "critical": 0,
            "high": 1,
            "medium": 3,
            "low": 5,
            "vulnerabilities": [
                {
                    "cve": "CVE-2023-1234",
                    "severity": "HIGH",
                    "package": "nginx",
                    "version": "1.20.0",
                    "fixed_version": "1.20.2",
                    "description": "HTTP request smuggling"
                }
            ]
        }
    else:
        return {
            "critical": 0,
            "high": 0,
            "medium": 2,
            "low": 4,
            "vulnerabilities": []
        }

async def perform_scan(image: str, scan_id: int):
    """Perform the actual vulnerability scan"""
    try:
        conn = sqlite3.connect('scanner.db')
        c = conn.cursor()
        
        # Update status to scanning
        c.execute('UPDATE scans SET status = ? WHERE id = ?', ('scanning', scan_id))
        conn.commit()
        
        # Perform scan
        results = await simulate_trivy_scan(image)
        
        # Generate image digest
        image_digest = hashlib.sha256(image.encode()).hexdigest()[:16]
        
        # Update scan results
        c.execute('''UPDATE scans SET 
                     status = ?,
                     image_digest = ?,
                     critical = ?,
                     high = ?,
                     medium = ?,
                     low = ?,
                     results = ?
                     WHERE id = ?''',
                  ('completed', 
                   image_digest,
                   results['critical'],
                   results['high'],
                   results['medium'],
                   results['low'],
                   json.dumps(results),
                   scan_id))
        conn.commit()
        conn.close()
        
    except Exception as e:
        conn = sqlite3.connect('scanner.db')
        c = conn.cursor()
        c.execute('UPDATE scans SET status = ? WHERE id = ?', ('failed', scan_id))
        conn.commit()
        conn.close()
        print(f"Scan failed: {e}")

@app.post("/scan", response_model=ScanResponse)
async def scan_image(request: ScanRequest, background_tasks: BackgroundTasks):
    """Scan a container image for vulnerabilities"""
    
    conn = sqlite3.connect('scanner.db')
    c = conn.cursor()
    
    # Create scan record
    scan_time = datetime.utcnow().isoformat()
    c.execute('INSERT INTO scans (image, scan_time, status) VALUES (?, ?, ?)',
              (request.image, scan_time, 'pending'))
    scan_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Start background scan
    background_tasks.add_task(perform_scan, request.image, scan_id)
    
    return ScanResponse(
        scan_id=scan_id,
        image=request.image,
        status="pending",
        message="Scan initiated"
    )

@app.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int):
    """Get scan results"""
    conn = sqlite3.connect('scanner.db')
    c = conn.cursor()
    c.execute('SELECT * FROM scans WHERE id = ?', (scan_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get policy
    conn = sqlite3.connect('scanner.db')
    c = conn.cursor()
    c.execute('SELECT * FROM policies WHERE active = 1 LIMIT 1')
    policy_row = c.fetchone()
    conn.close()
    
    blocked = False
    message = ""
    
    if policy_row and row[3] == 'completed':
        severity_threshold = policy_row[2]
        action = policy_row[3]
        
        if severity_threshold == 'CRITICAL' and row[4] > 0 and action == 'block':
            blocked = True
            message = f"Image blocked: {row[4]} CRITICAL vulnerabilities found"
        elif severity_threshold == 'HIGH' and (row[4] > 0 or row[5] > 0) and action == 'block':
            blocked = True
            message = f"Image blocked: {row[4]} CRITICAL, {row[5]} HIGH vulnerabilities found"
    
    return ScanResponse(
        scan_id=row[0],
        image=row[1],
        status=row[3],
        critical=row[4] or 0,
        high=row[5] or 0,
        medium=row[6] or 0,
        low=row[7] or 0,
        blocked=blocked,
        message=message or f"Scan {row[3]}"
    )

@app.get("/scans")
async def list_scans():
    """List all scans"""
    conn = sqlite3.connect('scanner.db')
    c = conn.cursor()
    c.execute('SELECT * FROM scans ORDER BY id DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    scans = []
    for row in rows:
        scans.append({
            "scan_id": row[0],
            "image": row[1],
            "scan_time": row[3],
            "status": row[4],
            "critical": row[5] or 0,
            "high": row[6] or 0,
            "medium": row[7] or 0,
            "low": row[8] or 0
        })
    
    return {"scans": scans}

@app.post("/policy")
async def create_policy(policy: PolicyModel):
    """Create or update security policy"""
    conn = sqlite3.connect('scanner.db')
    c = conn.cursor()
    
    c.execute('''INSERT OR REPLACE INTO policies (name, severity_threshold, action, active)
                 VALUES (?, ?, ?, ?)''',
              (policy.name, policy.severity_threshold, policy.action, 1 if policy.active else 0))
    conn.commit()
    conn.close()
    
    return {"message": "Policy created", "policy": policy.dict()}

@app.get("/policy")
async def get_policies():
    """Get all policies"""
    conn = sqlite3.connect('scanner.db')
    c = conn.cursor()
    c.execute('SELECT * FROM policies')
    rows = c.fetchall()
    conn.close()
    
    policies = []
    for row in rows:
        policies.append({
            "id": row[0],
            "name": row[1],
            "severity_threshold": row[2],
            "action": row[3],
            "active": bool(row[4])
        })
    
    return {"policies": policies}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "scanner"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
