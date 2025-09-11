import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from kubernetes import client, config
import boto3
from prometheus_client import Counter, Histogram, generate_latest
import yaml

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Enable CORS for all routes
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

class KubernetesManager:
    def __init__(self):
        self.mock_mode = os.getenv('K8S_MOCK_MODE', 'false').lower() == 'true'
        
        if self.mock_mode:
            logging.info("Running in mock mode - no Kubernetes cluster connection")
            self.v1 = None
            self.apps_v1 = None
            self.autoscaling_v1 = None
            self.metrics_v1 = None
        else:
            try:
                config.load_incluster_config()
                logging.info("Connected to Kubernetes cluster (in-cluster config)")
            except:
                try:
                    config.load_kube_config()
                    logging.info("Connected to Kubernetes cluster (kubeconfig)")
                except Exception as e:
                    logging.warning(f"Could not connect to Kubernetes cluster: {e}")
                    logging.info("Falling back to mock mode")
                    self.mock_mode = True
                    self.v1 = None
                    self.apps_v1 = None
                    self.autoscaling_v1 = None
                    self.metrics_v1 = None
                    return
            
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.autoscaling_v1 = client.AutoscalingV1Api()
            self.metrics_v1 = client.CustomObjectsApi()

    def get_cluster_info(self):
        """Get comprehensive cluster information"""
        if self.mock_mode:
            return self._get_mock_cluster_info()
        
        nodes = self.v1.list_node()
        pods = self.v1.list_pod_for_all_namespaces()
        
        cluster_info = {
            'nodes': {
                'total': len(nodes.items),
                'ready': sum(1 for node in nodes.items if self._is_node_ready(node)),
                'details': []
            },
            'pods': {
                'total': len(pods.items),
                'running': sum(1 for pod in pods.items if pod.status.phase == 'Running'),
                'pending': sum(1 for pod in pods.items if pod.status.phase == 'Pending'),
                'failed': sum(1 for pod in pods.items if pod.status.phase == 'Failed')
            },
            'namespaces': len(self.v1.list_namespace().items)
        }
        
        # Node details
        for node in nodes.items:
            node_info = {
                'name': node.metadata.name,
                'ready': self._is_node_ready(node),
                'instance_type': node.metadata.labels.get('node.kubernetes.io/instance-type', 'unknown'),
                'zone': node.metadata.labels.get('topology.kubernetes.io/zone', 'unknown'),
                'capacity': {
                    'cpu': node.status.capacity.get('cpu', '0'),
                    'memory': node.status.capacity.get('memory', '0'),
                    'pods': node.status.capacity.get('pods', '0')
                }
            }
            cluster_info['nodes']['details'].append(node_info)
        
        return cluster_info

    def _is_node_ready(self, node):
        for condition in node.status.conditions:
            if condition.type == 'Ready':
                return condition.status == 'True'
        return False

    def get_autoscaling_status(self):
        """Get HPA and cluster autoscaler status"""
        if self.mock_mode:
            return self._get_mock_autoscaling_status()
        
        hpas = self.autoscaling_v1.list_horizontal_pod_autoscaler_for_all_namespaces()
        
        scaling_info = {
            'hpas': [],
            'cluster_autoscaler': self._get_cluster_autoscaler_status()
        }
        
        for hpa in hpas.items:
            hpa_info = {
                'name': hpa.metadata.name,
                'namespace': hpa.metadata.namespace,
                'target_ref': hpa.spec.scale_target_ref.name,
                'min_replicas': hpa.spec.min_replicas,
                'max_replicas': hpa.spec.max_replicas,
                'current_replicas': hpa.status.current_replicas,
                'desired_replicas': hpa.status.desired_replicas
            }
            scaling_info['hpas'].append(hpa_info)
        
        return scaling_info

    def _get_cluster_autoscaler_status(self):
        if self.mock_mode:
            return {'status': 'Running', 'ready': True, 'restart_count': 0}
        
        try:
            pods = self.v1.list_namespaced_pod(
                namespace='kube-system',
                label_selector='app=cluster-autoscaler'
            )
            
            if pods.items:
                pod = pods.items[0]
                return {
                    'status': pod.status.phase,
                    'ready': pod.status.container_statuses[0].ready if pod.status.container_statuses else False,
                    'restart_count': pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0
                }
        except Exception as e:
            logging.error(f"Error getting cluster autoscaler status: {e}")
        
        return {'status': 'unknown', 'ready': False, 'restart_count': 0}

    def _get_mock_cluster_info(self):
        """Return mock cluster information for development"""
        return {
            'nodes': {
                'total': 3,
                'ready': 3,
                'details': [
                    {
                        'name': 'worker-node-1',
                        'ready': True,
                        'instance_type': 't3.medium',
                        'zone': 'us-west-2a',
                        'capacity': {'cpu': '2', 'memory': '4Gi', 'pods': '110'}
                    },
                    {
                        'name': 'worker-node-2',
                        'ready': True,
                        'instance_type': 't3.medium',
                        'zone': 'us-west-2b',
                        'capacity': {'cpu': '2', 'memory': '4Gi', 'pods': '110'}
                    },
                    {
                        'name': 'master-node',
                        'ready': True,
                        'instance_type': 't3.small',
                        'zone': 'us-west-2a',
                        'capacity': {'cpu': '1', 'memory': '2Gi', 'pods': '110'}
                    }
                ]
            },
            'pods': {
                'total': 15,
                'running': 12,
                'pending': 2,
                'failed': 1
            },
            'namespaces': 5
        }

    def _get_mock_autoscaling_status(self):
        """Return mock autoscaling information for development"""
        return {
            'hpas': [
                {
                    'name': 'web-app-hpa',
                    'namespace': 'default',
                    'target_ref': 'web-app-deployment',
                    'min_replicas': 2,
                    'max_replicas': 10,
                    'current_replicas': 3,
                    'desired_replicas': 3
                },
                {
                    'name': 'api-hpa',
                    'namespace': 'production',
                    'target_ref': 'api-deployment',
                    'min_replicas': 1,
                    'max_replicas': 5,
                    'current_replicas': 2,
                    'desired_replicas': 2
                }
            ],
            'cluster_autoscaler': {
                'status': 'Running',
                'ready': True,
                'restart_count': 0
            }
        }

    def _get_mock_network_policies(self):
        """Return mock network policies for development"""
        return {
            'policies': [
                {
                    'name': 'web-app-policy',
                    'namespace': 'default',
                    'pod_selector': {'matchLabels': {'app': 'web-app'}},
                    'ingress_rules': 2,
                    'egress_rules': 1
                },
                {
                    'name': 'api-policy',
                    'namespace': 'production',
                    'pod_selector': {'matchLabels': {'app': 'api'}},
                    'ingress_rules': 1,
                    'egress_rules': 2
                }
            ],
            'total': 2
        }

k8s_manager = KubernetesManager()

@app.route('/health')
def health():
    REQUEST_COUNT.labels(method='GET', endpoint='/health').inc()
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/cluster/info')
def cluster_info():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/cluster/info').inc()
    with REQUEST_DURATION.time():
        try:
            info = k8s_manager.get_cluster_info()
            return jsonify(info)
        except Exception as e:
            logging.error(f"Error getting cluster info: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/autoscaling/status')
def autoscaling_status():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/autoscaling/status').inc()
    with REQUEST_DURATION.time():
        try:
            status = k8s_manager.get_autoscaling_status()
            return jsonify(status)
        except Exception as e:
            logging.error(f"Error getting autoscaling status: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/network/policies')
def network_policies():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/network/policies').inc()
    with REQUEST_DURATION.time():
        try:
            if k8s_manager.mock_mode:
                return jsonify(k8s_manager._get_mock_network_policies())
            
            # Get network policies from all namespaces
            policies = k8s_manager.metrics_v1.list_cluster_custom_object(
                group='networking.k8s.io',
                version='v1',
                plural='networkpolicies'
            )
            
            policy_info = []
            for policy in policies.get('items', []):
                policy_data = {
                    'name': policy['metadata']['name'],
                    'namespace': policy['metadata']['namespace'],
                    'pod_selector': policy['spec'].get('podSelector', {}),
                    'ingress_rules': len(policy['spec'].get('ingress', [])),
                    'egress_rules': len(policy['spec'].get('egress', []))
                }
                policy_info.append(policy_data)
            
            return jsonify({'policies': policy_info, 'total': len(policy_info)})
        except Exception as e:
            logging.error(f"Error getting network policies: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    return generate_latest()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
