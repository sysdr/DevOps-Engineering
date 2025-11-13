import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.backup_manager import BackupManager, ReplicationManager, DRMetricsCollector

def test_backup_creation():
    manager = BackupManager()
    backup = manager.create_backup("test-backup", ["default"], "full")
    
    assert backup["name"] == "test-backup"
    assert backup["status"] == "completed"
    assert backup["resources_count"] > 0
    print("✅ test_backup_creation passed")

def test_backup_restore():
    manager = BackupManager()
    backup = manager.create_backup("test-backup", ["default"], "full")
    restore = manager.restore_backup(backup["id"], "dr")
    
    assert restore["status"] == "completed"
    assert restore["resources_restored"] == backup["resources_count"]
    print("✅ test_backup_restore passed")

def test_replication_status():
    manager = ReplicationManager()
    status = manager.get_status()
    
    assert "primary_region" in status
    assert "dr_region" in status
    assert status["enabled"] == True
    print("✅ test_replication_status passed")

def test_failover():
    manager = ReplicationManager()
    initial_primary = manager.replication_status["primary_region"]
    failover = manager.trigger_failover("us-west-2")
    
    assert failover["status"] == "completed"
    assert manager.replication_status["primary_region"] != initial_primary
    print("✅ test_failover passed")

def test_metrics():
    collector = DRMetricsCollector()
    metrics = collector.get_metrics()
    
    assert "rto_target_minutes" in metrics
    assert "rpo_target_minutes" in metrics
    assert metrics["backup_success_rate"] > 0
    print("✅ test_metrics passed")

if __name__ == "__main__":
    print("Running Disaster Recovery System Tests...\n")
    test_backup_creation()
    test_backup_restore()
    test_replication_status()
    test_failover()
    test_metrics()
    print("\n✅ All tests passed!")
