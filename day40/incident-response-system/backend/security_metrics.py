from datetime import datetime, timedelta
from typing import Dict, List
import statistics

class SecurityMetrics:
    def __init__(self):
        self.incidents = []
        self.detections = []
        self.false_positives = 0
        self.true_positives = 0
        
    def record_detection(self, event_time: datetime, detection_time: datetime, threat_score: int):
        """Record a detection with event time and detection time to calculate MTTD"""
        time_to_detect = (detection_time - event_time).total_seconds()
        self.detections.append({
            'event_time': event_time,
            'detection_time': detection_time,
            'time_to_detect_seconds': time_to_detect,
            'threat_score': threat_score
        })
    
    def record_incident(self, detection_time: datetime, response_time: datetime, severity: str, is_true_positive: bool = True):
        ttd = (response_time - detection_time).total_seconds()
        
        self.incidents.append({
            'detection_time': detection_time,
            'response_time': response_time,
            'ttd_seconds': ttd,
            'severity': severity,
            'is_true_positive': is_true_positive
        })
        
        if is_true_positive:
            self.true_positives += 1
        else:
            self.false_positives += 1
    
    def get_mttd(self) -> float:
        """Mean Time To Detect in seconds - time from event occurrence to detection"""
        if not self.detections:
            # If no detections yet, return a default value or 0
            return 0.0
        return statistics.mean([d['time_to_detect_seconds'] for d in self.detections])
    
    def get_mttr(self) -> float:
        """Mean Time To Respond in seconds"""
        if not self.incidents:
            return 0.0
        # Simulated response times
        return statistics.mean([i['ttd_seconds'] + 5 for i in self.incidents])
    
    def get_false_positive_rate(self) -> float:
        total = self.true_positives + self.false_positives
        if total == 0:
            return 0.0
        return (self.false_positives / total) * 100
    
    def get_coverage_percentage(self) -> float:
        # Simulated coverage
        return 98.5
    
    def get_incidents_by_severity(self) -> Dict[str, int]:
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for incident in self.incidents:
            severity = incident['severity']
            if severity in severity_counts:
                severity_counts[severity] += 1
        return severity_counts
    
    def get_recent_incidents(self, hours: int = 24) -> List[Dict]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            i for i in self.incidents 
            if i['detection_time'] > cutoff_time
        ]
    
    def get_metrics_summary(self) -> Dict:
        return {
            'mttd_seconds': round(self.get_mttd(), 2),
            'mttr_seconds': round(self.get_mttr(), 2),
            'false_positive_rate': round(self.get_false_positive_rate(), 2),
            'coverage_percentage': self.get_coverage_percentage(),
            'total_incidents': len(self.incidents),
            'total_detections': len(self.detections),
            'incidents_by_severity': self.get_incidents_by_severity(),
            'true_positives': self.true_positives,
            'false_positives': self.false_positives
        }

