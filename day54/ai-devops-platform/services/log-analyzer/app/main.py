from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from sklearn.ensemble import IsolationForest
import re

app = FastAPI(title="AI Log Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    source: str
    metadata: Optional[Dict] = {}

class AnomalyResult(BaseModel):
    log: LogEntry
    is_anomaly: bool
    anomaly_score: float
    reason: str

class LogAnalyzer:
    def __init__(self):
        self.log_buffer = deque(maxlen=1000)
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.is_trained = False
        self.error_patterns = {
            'out of memory': 'CRITICAL',
            'connection refused': 'HIGH',
            'timeout': 'MEDIUM',
            'deprecated': 'LOW',
            'warning': 'LOW'
        }
        self.baseline_metrics = {
            'error_rate': 0.05,
            'warning_rate': 0.15,
            'avg_msg_length': 100
        }
        
    def parse_log(self, log: LogEntry) -> np.ndarray:
        """Extract features from log entry"""
        features = []
        
        # Time-based features
        try:
            dt = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
            features.append(dt.hour)
            features.append(dt.minute)
            features.append(dt.weekday())
        except:
            features.extend([0, 0, 0])
        
        # Level encoding
        level_map = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
        features.append(level_map.get(log.level.upper(), 1))
        
        # Message features
        features.append(len(log.message))
        features.append(log.message.count('error'))
        features.append(log.message.count('failed'))
        features.append(log.message.count('exception'))
        
        # Pattern matching
        for pattern in self.error_patterns:
            features.append(1 if pattern in log.message.lower() else 0)
        
        return np.array(features).reshape(1, -1)
    
    def train_baseline(self):
        """Train anomaly detector on buffered logs"""
        if len(self.log_buffer) < 50:
            return False
        
        features = []
        for log in self.log_buffer:
            feat = self.parse_log(log)
            features.append(feat.flatten())
        
        X = np.array(features)
        self.anomaly_detector.fit(X)
        self.is_trained = True
        return True
    
    def detect_anomaly(self, log: LogEntry) -> AnomalyResult:
        """Detect if log entry is anomalous"""
        features = self.parse_log(log)
        
        # Add to buffer
        self.log_buffer.append(log)
        
        # Train if not trained and enough data
        if not self.is_trained and len(self.log_buffer) >= 50:
            self.train_baseline()
        
        if not self.is_trained:
            return AnomalyResult(
                log=log,
                is_anomaly=False,
                anomaly_score=0.0,
                reason="Collecting baseline data"
            )
        
        # Predict anomaly
        prediction = self.anomaly_detector.predict(features)[0]
        anomaly_score = -self.anomaly_detector.score_samples(features)[0]
        is_anomaly = prediction == -1
        
        # Determine reason
        reason = self._determine_reason(log, anomaly_score)
        
        return AnomalyResult(
            log=log,
            is_anomaly=is_anomaly,
            anomaly_score=float(anomaly_score),
            reason=reason
        )
    
    def _determine_reason(self, log: LogEntry, score: float) -> str:
        """Determine why log is anomalous"""
        if score < 0.3:
            return "Normal pattern"
        
        reasons = []
        
        # Check for known error patterns
        for pattern, severity in self.error_patterns.items():
            if pattern in log.message.lower():
                reasons.append(f"{severity} severity pattern: {pattern}")
        
        # Check unusual characteristics
        if len(log.message) > 500:
            reasons.append("Unusually long message")
        
        if log.level.upper() in ['ERROR', 'CRITICAL']:
            reasons.append(f"{log.level} level detected")
        
        if not reasons:
            reasons.append("Statistical anomaly detected")
        
        return " | ".join(reasons)

analyzer = LogAnalyzer()
active_connections: List[WebSocket] = []

@app.post("/ingest", response_model=AnomalyResult)
async def ingest_log(log: LogEntry):
    """Ingest a single log entry and analyze for anomalies"""
    result = analyzer.detect_anomaly(log)
    
    # Broadcast to WebSocket clients
    for connection in active_connections:
        try:
            await connection.send_json(result.dict())
        except:
            pass
    
    return result

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/stats")
async def get_statistics():
    """Get current log statistics"""
    if len(analyzer.log_buffer) == 0:
        return {
            "total_logs": 0,
            "is_trained": False,
            "buffer_size": 0
        }
    
    levels = {}
    for log in analyzer.log_buffer:
        levels[log.level] = levels.get(log.level, 0) + 1
    
    return {
        "total_logs": len(analyzer.log_buffer),
        "is_trained": analyzer.is_trained,
        "buffer_size": len(analyzer.log_buffer),
        "level_distribution": levels
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "log-analyzer"}
