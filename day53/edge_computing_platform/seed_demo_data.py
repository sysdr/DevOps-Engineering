#!/usr/bin/env python3
"""
Script to seed demo data for the Edge Computing Platform dashboard
Deploys sample models to show data in the dashboard
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000/api"

def seed_demo_data():
    """Deploy demo models to show in dashboard"""
    print("Seeding demo data...")
    
    deployments = [
        {
            "model_id": "object-detection-v2",
            "version": "2.1.0",
            "optimization": "full",
            "selector": {"gpu": True}  # Deploy to GPU-capable devices (datacenter)
        },
        {
            "model_id": "quality-control",
            "version": "1.5.0",
            "optimization": "quantized",
            "selector": {}  # Deploy to all devices
        },
        {
            "model_id": "anomaly-detection",
            "version": "3.0.0",
            "optimization": "ultra-light",
            "selector": {"gpu": False}  # Deploy to CPU-only devices (factory, mobile)
        }
    ]
    
    results = []
    for deployment in deployments:
        try:
            response = requests.post(
                f"{API_BASE}/models/deploy",
                json=deployment,
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                results.append(result)
                print(f"✓ Deployed {deployment['model_id']} v{deployment['version']} "
                      f"({deployment['optimization']}) to {len(result.get('target_devices', []))} devices")
            else:
                print(f"✗ Failed to deploy {deployment['model_id']}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"✗ Error deploying {deployment['model_id']}: {e}")
            sys.exit(1)
    
    print(f"\n✅ Successfully deployed {len(results)} demo models!")
    print("\nDashboard will now show:")
    print("  - Model deployments")
    print("  - Deployment history")
    print("  - Models across devices")
    print("\nView at: http://localhost:8000/")

if __name__ == "__main__":
    seed_demo_data()

