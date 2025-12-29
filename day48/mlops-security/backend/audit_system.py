import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class AuditSystem:
    def __init__(self):
        self.chain = []
        self.event_count = 0
    
    def log_event(self, event: Dict[str, Any]) -> str:
        """Log event to immutable audit chain"""
        
        # Get previous hash
        prev_hash = self.chain[-1]["hash"] if self.chain else "0" * 64
        
        # Create event record
        record = {
            "id": self.event_count,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event.get("type"),
            "details": event,
            "previous_hash": prev_hash
        }
        
        # Calculate hash
        record_str = json.dumps(record, sort_keys=True)
        current_hash = hashlib.sha256(record_str.encode()).hexdigest()
        record["hash"] = current_hash
        
        # Append to chain
        self.chain.append(record)
        self.event_count += 1
        
        return current_hash
    
    def get_events(self, limit: int = 10, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent audit events"""
        events = self.chain[-limit:]
        
        if model_id:
            events = [e for e in events if e.get("details", {}).get("model_id") == model_id]
        
        return events
    
    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Verify cryptographic integrity of audit chain"""
        
        for i in range(len(self.chain)):
            event = self.chain[i]
            
            # Verify hash
            event_copy = {k: v for k, v in event.items() if k != "hash"}
            expected_hash = hashlib.sha256(json.dumps(event_copy, sort_keys=True).encode()).hexdigest()
            
            if expected_hash != event["hash"]:
                return {
                    "valid": False,
                    "tampered_event": i,
                    "message": "Event hash mismatch"
                }
            
            # Verify chain linkage
            if i > 0:
                if event["previous_hash"] != self.chain[i-1]["hash"]:
                    return {
                        "valid": False,
                        "break_at": i,
                        "message": "Chain linkage broken"
                    }
        
        return {
            "valid": True,
            "total_events": len(self.chain),
            "verified_at": datetime.utcnow().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics"""
        event_types = {}
        for event in self.chain:
            etype = event.get("event_type", "unknown")
            event_types[etype] = event_types.get(etype, 0) + 1
        
        return {
            "total_events": len(self.chain),
            "by_type": event_types
        }
