import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.edge_controller import EdgeController

def test_device_registration():
    controller = EdgeController()
    
    device_id = controller.register_device(
        {"name": "Test Device", "lat": 37.7749, "lon": -122.4194},
        ["gpu", "high-memory"]
    )
    
    assert device_id is not None
    assert device_id in controller.devices
    print("✓ Device registration test passed")

def test_heartbeat_processing():
    controller = EdgeController()
    
    device_id = controller.register_device(
        {"name": "Test", "lat": 0, "lon": 0},
        ["cpu-only"]
    )
    
    result = controller.process_heartbeat(device_id, {
        "cpu_percent": 50,
        "memory_percent": 60,
        "disk_percent": 40
    })
    
    assert result["status"] == "ok"
    print("✓ Heartbeat processing test passed")

def test_model_deployment():
    controller = EdgeController()
    
    # Register devices
    device_id1 = controller.register_device(
        {"name": "GPU Device", "lat": 0, "lon": 0},
        ["gpu"]
    )
    device_id2 = controller.register_device(
        {"name": "CPU Device", "lat": 0, "lon": 0},
        ["cpu-only"]
    )
    
    # Mark as ready
    from models.edge_device import DeviceStatus
    controller.devices[device_id1].status = DeviceStatus.READY
    controller.devices[device_id2].status = DeviceStatus.READY
    
    # Deploy to GPU devices only
    result = controller.deploy_model(
        "resnet50",
        "1.3",
        "full",
        {"gpu": True}
    )
    
    assert len(result["target_devices"]) == 1
    assert device_id1 in result["target_devices"]
    print("✓ Model deployment test passed")

def test_fleet_status():
    controller = EdgeController()
    
    controller.register_device({"name": "D1", "lat": 0, "lon": 0}, ["gpu"])
    controller.register_device({"name": "D2", "lat": 0, "lon": 0}, ["cpu"])
    
    status = controller.get_fleet_status()
    
    assert status["total_devices"] == 2
    print("✓ Fleet status test passed")

if __name__ == "__main__":
    test_device_registration()
    test_heartbeat_processing()
    test_model_deployment()
    test_fleet_status()
    print("\n✅ All tests passed!")
