from fastapi import APIRouter
from typing import List
from ..services.anomaly_detector import AnomalyDetector
from ..models.alert_models import Alert

router = APIRouter()
detector = AnomalyDetector()

# Flag to track if anomaly check has been done
_anomaly_check_done = False

async def ensure_anomaly_check():
    """Ensure anomaly check has been performed at least once"""
    global _anomaly_check_done
    if not _anomaly_check_done:
        try:
            await detector.check_anomalies()
            _anomaly_check_done = True
        except Exception as e:
            print(f"Error in initial anomaly check: {e}")

@router.get("/")
async def get_alerts():
    """Get all active alerts"""
    # Always check for new anomalies when alerts are requested
    # Run multiple checks to increase chance of detecting anomalies
    try:
        for _ in range(5):  # Run 5 checks to increase detection chance
            await detector.check_anomalies()
    except Exception as e:
        print(f"Error checking anomalies: {e}")
    
    alerts = detector.get_recent_anomalies()
    
    # If no alerts exist, return empty array (component will show "No active alerts")
    # This is correct behavior - shows that monitoring is active but no issues detected
    return {"alerts": alerts}

@router.get("/history")
async def get_alert_history(days: int = 7):
    """Get alert history"""
    return {"alerts": detector.get_anomaly_history(days)}

@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    detector.acknowledge_anomaly(alert_id)
    return {"status": "acknowledged", "alert_id": alert_id}
