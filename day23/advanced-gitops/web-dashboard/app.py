from flask import Flask, render_template, jsonify
import yaml
import requests
import json
from datetime import datetime, timedelta
import os
import time
import random

app = Flask(__name__)

class GitOpsMonitor:
    def __init__(self):
        self.argocd_api = "http://localhost:8080/api/v1"
        self.start_time = time.time()
        
    def get_applications_status(self):
        """Get status of all applications with dynamic metrics"""
        try:
            # Generate dynamic metrics based on time
            now = datetime.now()
            time_offset = int((time.time() - self.start_time) / 10) % 100
            
            # Dynamic health status that changes over time
            health_statuses = ["Healthy", "Progressing", "Degraded", "Suspended"]
            sync_statuses = ["Synced", "OutOfSync", "Unknown"]
            
            return {
                "app-of-apps": {
                    "health": health_statuses[time_offset % 2],  # Alternates between Healthy and Progressing
                    "sync": sync_statuses[0] if time_offset % 3 == 0 else sync_statuses[1],
                    "environment": "production",
                    "last_sync": (now - timedelta(minutes=5 + (time_offset % 30))).isoformat() + "Z",
                    "replicas": max(1, 3 + (time_offset % 5)),
                    "ready_replicas": max(1, 2 + (time_offset % 4))
                },
                "monitoring-stack": {
                    "health": "Healthy", 
                    "sync": "Synced",
                    "environment": "production",
                    "last_sync": (now - timedelta(minutes=10 + (time_offset % 20))).isoformat() + "Z",
                    "replicas": max(1, 2 + (time_offset % 3)),
                    "ready_replicas": max(1, 2 + (time_offset % 2))
                },
                "sample-app-dev": {
                    "health": health_statuses[(time_offset + 1) % 3],
                    "sync": sync_statuses[time_offset % 2], 
                    "environment": "dev",
                    "last_sync": (now - timedelta(minutes=15 + (time_offset % 25))).isoformat() + "Z",
                    "replicas": max(1, 1 + (time_offset % 4)),
                    "ready_replicas": max(1, (time_offset % 3))
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_rollout_status(self):
        """Get rollout status with dynamic metrics"""
        time_offset = int((time.time() - self.start_time) / 15) % 20
        
        # Dynamic canary steps (0-4 steps)
        current_step_num = time_offset % 5
        total_steps = 4
        replicas = max(3, 5 + (time_offset % 3))
        ready_replicas = max(2, replicas - (time_offset % 2))
        canary_weight = (current_step_num * 20) % 100
        
        # Status changes as rollout progresses
        if current_step_num == total_steps:
            status = "Complete"
        elif current_step_num == 0:
            status = "Initializing"
        else:
            status = "Progressing"
        
        return {
            "sample-app-rollout": {
                "replicas": replicas,
                "ready_replicas": ready_replicas,
                "current_step": f"{current_step_num}/{total_steps}",
                "canary_weight": f"{canary_weight}%",
                "status": status,
                "updated_at": datetime.now().isoformat() + "Z"
            }
        }
    
    def get_applicationset_status(self):
        """Get ApplicationSet generated applications with dynamic metrics"""
        time_offset = int((time.time() - self.start_time) / 20) % 10
        generated_apps = max(3, 3 + (time_offset % 3))
        environments = ["dev", "staging", "prod"]
        
        return {
            "multi-env-applications": {
                "generated_apps": generated_apps,
                "environments": environments,
                "last_update": (datetime.now() - timedelta(seconds=time_offset * 2)).isoformat() + "Z",
                "total_deployments": max(9, 9 + (time_offset % 5)),
                "successful_deployments": max(8, 8 + (time_offset % 4))
            }
        }

@app.route('/')
def dashboard():
    monitor = GitOpsMonitor()
    
    context = {
        'title': 'Advanced GitOps Dashboard',
        'applications': monitor.get_applications_status(),
        'rollouts': monitor.get_rollout_status(),
        'applicationsets': monitor.get_applicationset_status(),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('dashboard.html', **context)

@app.route('/api/status')
def api_status():
    monitor = GitOpsMonitor()
    
    return jsonify({
        'applications': monitor.get_applications_status(),
        'rollouts': monitor.get_rollout_status(),
        'applicationsets': monitor.get_applicationset_status()
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
