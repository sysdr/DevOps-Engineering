from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import time
import numpy as np
import logging
from logging_config import setup_logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = setup_logger("anomaly-detector")

class AnomalyDetector:
    def __init__(self, es_host='localhost', es_port=9200):
        self.es = Elasticsearch([f'http://{es_host}:{es_port}'])
        self.baseline_window = 30  # minutes
        self.check_interval = 60  # seconds
        
    def get_error_rate(self, minutes_ago):
        """Calculate error rate for a given time window"""
        end_time = datetime.utcnow() - timedelta(minutes=minutes_ago)
        start_time = end_time - timedelta(minutes=5)
        
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": {
                            "gte": start_time.isoformat(),
                            "lte": end_time.isoformat()
                        }}}
                    ]
                }
            },
            "aggs": {
                "total_logs": {"value_count": {"field": "level.keyword"}},
                "error_logs": {
                    "filter": {
                        "terms": {"level.keyword": ["ERROR", "WARN"]}
                    }
                }
            }
        }
        
        try:
            result = self.es.search(index="logs-production-*", body=query)
            total = result['aggregations']['total_logs']['value']
            errors = result['aggregations']['error_logs']['doc_count']
            
            if total == 0:
                return 0.0
            
            return (errors / total) * 100
        except Exception as e:
            logger.error(f"Failed to calculate error rate: {e}")
            return 0.0
    
    def detect_anomalies(self):
        """Detect anomalies using statistical baseline"""
        # Calculate baseline (last 30 minutes)
        baseline_rates = []
        for i in range(6, 36, 5):  # 6 data points over 30 minutes
            rate = self.get_error_rate(i)
            if rate > 0:
                baseline_rates.append(rate)
        
        if len(baseline_rates) < 3:
            logger.warning("Insufficient baseline data for anomaly detection")
            return False, None
        
        baseline_mean = np.mean(baseline_rates)
        baseline_std = np.std(baseline_rates)
        
        # Get current error rate
        current_rate = self.get_error_rate(0)
        
        # Anomaly threshold: mean + 3 * std_dev
        threshold = baseline_mean + (3 * baseline_std)
        
        is_anomaly = current_rate > threshold
        
        if is_anomaly:
            logger.warning("Anomaly detected!", extra={
                "event": "anomaly_detected",
                "current_error_rate": round(current_rate, 2),
                "baseline_mean": round(baseline_mean, 2),
                "baseline_std": round(baseline_std, 2),
                "threshold": round(threshold, 2),
                "deviation": round(current_rate - baseline_mean, 2)
            })
        else:
            logger.info("No anomaly detected", extra={
                "event": "anomaly_check",
                "current_error_rate": round(current_rate, 2),
                "baseline_mean": round(baseline_mean, 2),
                "threshold": round(threshold, 2)
            })
        
        return is_anomaly, {
            "current_rate": round(current_rate, 2),
            "baseline_mean": round(baseline_mean, 2),
            "baseline_std": round(baseline_std, 2),
            "threshold": round(threshold, 2),
            "is_anomaly": is_anomaly
        }
    
    def run_continuous_detection(self):
        """Run continuous anomaly detection"""
        logger.info("Starting continuous anomaly detection")
        
        while True:
            try:
                is_anomaly, metrics = self.detect_anomalies()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Stopping anomaly detector")
                break
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    detector = AnomalyDetector(es_host='localhost', es_port=9200)
    detector.run_continuous_detection()
