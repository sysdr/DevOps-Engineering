from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import asyncio
import json
import sqlite3

app = FastAPI(title="Runtime Security Monitor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections: List[WebSocket] = []

# Database initialization
def init_db():
    conn = sqlite3.connect('runtime.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT NOT NULL,
                  severity TEXT NOT NULL,
                  rule TEXT NOT NULL,
                  pod_name TEXT,
                  namespace TEXT,
                  container TEXT,
                  command TEXT,
                  message TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS rules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  description TEXT,
                  condition TEXT NOT NULL,
                  severity TEXT NOT NULL,
                  enabled INTEGER DEFAULT 1)''')
    
    # Insert default Falco-like rules
    default_rules = [
        ("Shell in Container", "Detect shell spawned in container", "spawned_process = /bin/bash", "WARNING", 1),
        ("Sensitive File Read", "Detect read of sensitive files", "file_access = /etc/shadow", "CRITICAL", 1),
        ("Outbound Connection", "Detect unexpected network connection", "network_connection = external", "INFO", 1),
        ("Privilege Escalation", "Detect privilege escalation attempt", "setuid_call = true", "CRITICAL", 1),
        ("Write to Binary Dir", "Detect write to system binaries", "file_write = /bin/*", "HIGH", 1)
    ]
    
    for rule in default_rules:
        c.execute('INSERT OR IGNORE INTO rules (name, description, condition, severity, enabled) VALUES (?, ?, ?, ?, ?)', rule)
    
    conn.commit()
    conn.close()

init_db()

class Alert(BaseModel):
    severity: str
    rule: str
    pod_name: str
    namespace: str
    container: str
    command: str
    message: str

# Simulate Falco-like behavior monitoring
async def simulate_runtime_monitoring():
    """Simulate runtime security events"""
    scenarios = [
        {
            "severity": "WARNING",
            "rule": "Shell in Container",
            "pod_name": "nginx-deployment-7d6b8c9f5d-abc12",
            "namespace": "default",
            "container": "nginx",
            "command": "/bin/bash",
            "message": "Shell spawned in container (user=www-data)"
        },
        {
            "severity": "CRITICAL",
            "rule": "Sensitive File Read",
            "pod_name": "app-server-6c8d9e7f4g-xyz89",
            "namespace": "production",
            "container": "app",
            "command": "cat /etc/shadow",
            "message": "Attempt to read /etc/shadow"
        },
        {
            "severity": "INFO",
            "rule": "Outbound Connection",
            "pod_name": "web-frontend-5b7c8d6e3f-def45",
            "namespace": "default",
            "container": "web",
            "command": "curl http://external-api.com",
            "message": "Outbound connection to 104.26.10.78:443"
        },
        {
            "severity": "HIGH",
            "rule": "Write to Binary Dir",
            "pod_name": "worker-pod-4a6b7c5d2e-ghi78",
            "namespace": "default",
            "container": "worker",
            "command": "cp malicious /bin/",
            "message": "Write attempt to /bin directory"
        }
    ]
    
    while True:
        await asyncio.sleep(15)  # Generate alerts every 15 seconds
        
        import random
        alert_data = random.choice(scenarios)
        alert_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Store in database
        conn = sqlite3.connect('runtime.db')
        c = conn.cursor()
        c.execute('''INSERT INTO alerts (timestamp, severity, rule, pod_name, namespace, container, command, message)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (alert_data["timestamp"], alert_data["severity"], alert_data["rule"],
                   alert_data["pod_name"], alert_data["namespace"], alert_data["container"],
                   alert_data["command"], alert_data["message"]))
        conn.commit()
        conn.close()
        
        # Broadcast to WebSocket clients
        for connection in active_connections:
            try:
                await connection.send_json(alert_data)
            except:
                pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulate_runtime_monitoring())

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/alerts")
async def get_alerts(limit: int = 50):
    """Get recent alerts"""
    conn = sqlite3.connect('runtime.db')
    c = conn.cursor()
    c.execute('SELECT * FROM alerts ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    
    alerts = []
    for row in rows:
        alerts.append({
            "id": row[0],
            "timestamp": row[1],
            "severity": row[2],
            "rule": row[3],
            "pod_name": row[4],
            "namespace": row[5],
            "container": row[6],
            "command": row[7],
            "message": row[8]
        })
    
    return {"alerts": alerts}

@app.get("/rules")
async def get_rules():
    """Get security rules"""
    conn = sqlite3.connect('runtime.db')
    c = conn.cursor()
    c.execute('SELECT * FROM rules WHERE enabled = 1')
    rows = c.fetchall()
    conn.close()
    
    rules = []
    for row in rows:
        rules.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "condition": row[3],
            "severity": row[4],
            "enabled": bool(row[5])
        })
    
    return {"rules": rules}

@app.get("/stats")
async def get_stats():
    """Get alert statistics"""
    conn = sqlite3.connect('runtime.db')
    c = conn.cursor()
    
    # Count by severity
    c.execute("SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
    severity_counts = dict(c.fetchall())
    
    # Recent alert count
    c.execute("SELECT COUNT(*) FROM alerts WHERE timestamp > datetime('now', '-1 hour')")
    recent_count = c.fetchone()[0]
    
    conn.close()
    
    return {
        "severity_counts": severity_counts,
        "recent_count": recent_count,
        "total_rules": 5
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "runtime-monitor"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
