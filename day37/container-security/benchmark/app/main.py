from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import asyncio
import json
import sqlite3

app = FastAPI(title="CIS Benchmark Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_db():
    conn = sqlite3.connect('benchmark.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS benchmarks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT NOT NULL,
                  total_checks INTEGER,
                  passed INTEGER,
                  failed INTEGER,
                  warnings INTEGER,
                  score REAL,
                  results TEXT)''')
    
    # Insert initial benchmark
    initial_results = {
        "checks": [
            {"id": "1.1.1", "description": "Ensure API server auth configured", "status": "PASS"},
            {"id": "1.1.2", "description": "Ensure API server TLS enabled", "status": "PASS"},
            {"id": "1.2.1", "description": "Ensure etcd is encrypted", "status": "PASS"},
            {"id": "1.2.2", "description": "Ensure etcd TLS enabled", "status": "PASS"},
            {"id": "2.1.1", "description": "Ensure kubelet auth configured", "status": "WARN"},
            {"id": "2.1.2", "description": "Ensure kubelet read-only port disabled", "status": "FAIL"},
            {"id": "3.1.1", "description": "Ensure network policies exist", "status": "PASS"},
            {"id": "4.1.1", "description": "Ensure pod security policies", "status": "FAIL"},
            {"id": "5.1.1", "description": "Ensure RBAC configured", "status": "PASS"},
            {"id": "5.2.1", "description": "Ensure service accounts limited", "status": "WARN"}
        ]
    }
    
    passed = sum(1 for c in initial_results["checks"] if c["status"] == "PASS")
    failed = sum(1 for c in initial_results["checks"] if c["status"] == "FAIL")
    warnings = sum(1 for c in initial_results["checks"] if c["status"] == "WARN")
    total = len(initial_results["checks"])
    score = (passed / total) * 100
    
    c.execute('''INSERT INTO benchmarks (timestamp, total_checks, passed, failed, warnings, score, results)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (datetime.utcnow().isoformat(), total, passed, failed, warnings, score, json.dumps(initial_results)))
    
    conn.commit()
    conn.close()

init_db()

class BenchmarkResponse(BaseModel):
    id: int
    timestamp: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    score: float

async def run_benchmark():
    """Simulate CIS benchmark execution"""
    await asyncio.sleep(3)
    
    # Simulate benchmark results
    checks = [
        {"id": "1.1.1", "description": "Ensure API server auth configured", "status": "PASS"},
        {"id": "1.1.2", "description": "Ensure API server TLS enabled", "status": "PASS"},
        {"id": "1.2.1", "description": "Ensure etcd is encrypted", "status": "PASS"},
        {"id": "1.2.2", "description": "Ensure etcd TLS enabled", "status": "PASS"},
        {"id": "2.1.1", "description": "Ensure kubelet auth configured", "status": "WARN"},
        {"id": "2.1.2", "description": "Ensure kubelet read-only port disabled", "status": "FAIL"},
        {"id": "3.1.1", "description": "Ensure network policies exist", "status": "PASS"},
        {"id": "4.1.1", "description": "Ensure pod security policies", "status": "FAIL"},
        {"id": "5.1.1", "description": "Ensure RBAC configured", "status": "PASS"},
        {"id": "5.2.1", "description": "Ensure service accounts limited", "status": "WARN"}
    ]
    
    results = {"checks": checks}
    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")
    warnings = sum(1 for c in checks if c["status"] == "WARN")
    total = len(checks)
    score = (passed / total) * 100
    
    conn = sqlite3.connect('benchmark.db')
    c = conn.cursor()
    c.execute('''INSERT INTO benchmarks (timestamp, total_checks, passed, failed, warnings, score, results)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (datetime.utcnow().isoformat(), total, passed, failed, warnings, score, json.dumps(results)))
    benchmark_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return benchmark_id

@app.post("/benchmark/run")
async def start_benchmark():
    """Start a new CIS benchmark run"""
    benchmark_id = await run_benchmark()
    
    return {
        "message": "Benchmark completed",
        "benchmark_id": benchmark_id
    }

@app.get("/benchmark/latest", response_model=BenchmarkResponse)
async def get_latest_benchmark():
    """Get latest benchmark results"""
    conn = sqlite3.connect('benchmark.db')
    c = conn.cursor()
    c.execute('SELECT * FROM benchmarks ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"error": "No benchmarks found"}
    
    return BenchmarkResponse(
        id=row[0],
        timestamp=row[1],
        total_checks=row[2],
        passed=row[3],
        failed=row[4],
        warnings=row[5],
        score=row[6]
    )

@app.get("/benchmark/{benchmark_id}")
async def get_benchmark(benchmark_id: int):
    """Get specific benchmark results with details"""
    conn = sqlite3.connect('benchmark.db')
    c = conn.cursor()
    c.execute('SELECT * FROM benchmarks WHERE id = ?', (benchmark_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"error": "Benchmark not found"}
    
    return {
        "id": row[0],
        "timestamp": row[1],
        "total_checks": row[2],
        "passed": row[3],
        "failed": row[4],
        "warnings": row[5],
        "score": row[6],
        "details": json.loads(row[7])
    }

@app.get("/benchmark/history")
async def get_benchmark_history():
    """Get benchmark history"""
    conn = sqlite3.connect('benchmark.db')
    c = conn.cursor()
    c.execute('SELECT id, timestamp, total_checks, passed, failed, warnings, score FROM benchmarks ORDER BY id DESC LIMIT 20')
    rows = c.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "timestamp": row[1],
            "total_checks": row[2],
            "passed": row[3],
            "failed": row[4],
            "warnings": row[5],
            "score": row[6]
        })
    
    return {"history": history}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "benchmark"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
