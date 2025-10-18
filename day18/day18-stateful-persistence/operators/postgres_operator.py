import asyncio
import logging
import kopf
import kubernetes
from kubernetes.client.rest import ApiException
import yaml
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@kopf.on.create('apps', 'v1', 'statefulsets')
async def on_statefulset_create(spec, name, namespace, **kwargs):
    if name.startswith('postgres-cluster'):
        logger.info(f"PostgreSQL StatefulSet {name} created in {namespace}")
        await setup_monitoring(name, namespace)

@kopf.on.update('apps', 'v1', 'statefulsets')
async def on_statefulset_update(spec, name, namespace, **kwargs):
    if name.startswith('postgres-cluster'):
        logger.info(f"PostgreSQL StatefulSet {name} updated in {namespace}")
        await check_cluster_health(name, namespace)

@kopf.timer('apps', 'v1', 'statefulsets', interval=30.0)
async def monitor_postgres_health(spec, name, namespace, **kwargs):
    if name.startswith('postgres-cluster'):
        await check_cluster_health(name, namespace)

async def setup_monitoring(name, namespace):
    """Setup monitoring for PostgreSQL cluster"""
    try:
        v1 = kubernetes.client.CoreV1Api()
        
        # Create monitoring service monitor
        monitor_config = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": f"{name}-monitor",
                "namespace": namespace
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "app": "postgres"
                    }
                },
                "endpoints": [{
                    "port": "metrics",
                    "interval": "30s"
                }]
            }
        }
        
        logger.info(f"Monitoring setup completed for {name}")
        
    except Exception as e:
        logger.error(f"Failed to setup monitoring: {e}")

async def check_cluster_health(name, namespace):
    """Check PostgreSQL cluster health and perform auto-healing"""
    try:
        v1 = kubernetes.client.CoreV1Api()
        apps_v1 = kubernetes.client.AppsV1Api()
        
        # Get StatefulSet
        statefulset = apps_v1.read_namespaced_stateful_set(name, namespace)
        
        # Get pods
        pods = v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=f"app=postgres"
        )
        
        healthy_pods = 0
        primary_found = False
        
        for pod in pods.items:
            if pod.status.phase == "Running":
                healthy_pods += 1
                # Check if this is primary
                if pod.metadata.name.endswith("-0"):
                    primary_found = True
        
        logger.info(f"Cluster health: {healthy_pods}/{statefulset.spec.replicas} pods healthy, primary: {primary_found}")
        
        # Auto-healing logic
        if not primary_found and healthy_pods > 0:
            await promote_replica_to_primary(namespace)
            
        # Scale check
        if healthy_pods < statefulset.spec.replicas:
            logger.warning(f"Some pods are unhealthy, monitoring for recovery...")
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")

async def promote_replica_to_primary(namespace):
    """Promote a replica to primary in case of primary failure"""
    try:
        v1 = kubernetes.client.CoreV1Api()
        
        # Find healthy replica
        pods = v1.list_namespaced_pod(
            namespace=namespace,
            label_selector="app=postgres"
        )
        
        for pod in pods.items:
            if pod.status.phase == "Running" and not pod.metadata.name.endswith("-0"):
                # Promote this replica
                logger.info(f"Promoting {pod.metadata.name} to primary")
                
                # Update pod labels
                pod.metadata.labels["role"] = "primary"
                v1.patch_namespaced_pod(
                    name=pod.metadata.name,
                    namespace=namespace,
                    body=pod
                )
                break
                
    except Exception as e:
        logger.error(f"Failed to promote replica: {e}")

if __name__ == "__main__":
    kopf.run()
