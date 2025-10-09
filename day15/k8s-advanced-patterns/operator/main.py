import kopf
import kubernetes
import asyncio
import logging
import yaml
from typing import Dict, Any
from kubernetes import client, config
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import os

# Metrics
WEBAPP_CREATED = Counter('webapp_created_total', 'Total WebApps created')
WEBAPP_DELETED = Counter('webapp_deleted_total', 'Total WebApps deleted')
WEBAPP_RECONCILED = Counter('webapp_reconciled_total', 'Total WebApp reconciliations')
WEBAPP_CURRENT = Gauge('webapp_current', 'Current number of WebApps')
RECONCILE_DURATION = Histogram('webapp_reconcile_duration_seconds', 'Time spent reconciling WebApps')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Kubernetes config
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
policy_v1 = client.PolicyV1Api()

class WebAppOperator:
    def __init__(self):
        self.metrics_port = int(os.environ.get('METRICS_PORT', 8000))
        start_http_server(self.metrics_port)
        logger.info(f"Metrics server started on port {self.metrics_port}")

    async def create_deployment(self, name: str, namespace: str, spec: Dict[str, Any]) -> None:
        """Create Kubernetes deployment for WebApp"""
        
        # Build affinity rules
        affinity = None
        if 'affinity' in spec:
            affinity = client.V1Affinity(
                node_affinity=client.V1NodeAffinity(
                    required_during_scheduling_ignored_during_execution=client.V1NodeSelector(
                        node_selector_terms=[
                            client.V1NodeSelectorTerm(
                                match_expressions=[
                                    client.V1NodeSelectorRequirement(
                                        key="topology.kubernetes.io/zone",
                                        operator="In",
                                        values=[spec['affinity'].get('zone', 'us-west-2a')]
                                    )
                                ]
                            )
                        ]
                    )
                ),
                pod_anti_affinity=client.V1PodAntiAffinity(
                    preferred_during_scheduling_ignored_during_execution=[
                        client.V1WeightedPodAffinityTerm(
                            weight=100,
                            pod_affinity_term=client.V1PodAffinityTerm(
                                label_selector=client.V1LabelSelector(
                                    match_labels={"app": name}
                                ),
                                topology_key="kubernetes.io/hostname"
                            )
                        )
                    ]
                )
            )

        resources = client.V1ResourceRequirements(
            requests={
                "cpu": spec.get('resources', {}).get('cpu', '100m'),
                "memory": spec.get('resources', {}).get('memory', '128Mi')
            },
            limits={
                "cpu": spec.get('resources', {}).get('cpu', '100m'),
                "memory": spec.get('resources', {}).get('memory', '128Mi')
            }
        )

        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=namespace,
                labels={"app": name, "managed-by": "webapp-operator"}
            ),
            spec=client.V1DeploymentSpec(
                replicas=spec['replicas'],
                selector=client.V1LabelSelector(
                    match_labels={"app": name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": name}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=name,
                                image=spec['image'],
                                ports=[client.V1ContainerPort(container_port=spec.get('port', 8080))],
                                resources=resources,
                                liveness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path="/health",
                                        port=spec.get('port', 8080)
                                    ),
                                    initial_delay_seconds=30,
                                    period_seconds=10
                                ),
                                readiness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path="/ready",
                                        port=spec.get('port', 8080)
                                    ),
                                    initial_delay_seconds=5,
                                    period_seconds=5
                                )
                            )
                        ],
                        affinity=affinity
                    )
                )
            )
        )

        try:
            apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
            logger.info(f"Created deployment {name} in namespace {namespace}")
        except client.exceptions.ApiException as e:
            if e.status == 409:  # Already exists
                apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
                logger.info(f"Updated deployment {name} in namespace {namespace}")
            else:
                raise

    async def create_service(self, name: str, namespace: str, spec: Dict[str, Any]) -> None:
        """Create Kubernetes service for WebApp"""
        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=f"{name}-service",
                namespace=namespace,
                labels={"app": name}
            ),
            spec=client.V1ServiceSpec(
                selector={"app": name},
                ports=[
                    client.V1ServicePort(
                        port=80,
                        target_port=spec.get('port', 8080),
                        protocol="TCP"
                    )
                ],
                type="ClusterIP"
            )
        )

        try:
            v1.create_namespaced_service(namespace=namespace, body=service)
            logger.info(f"Created service {name}-service in namespace {namespace}")
        except client.exceptions.ApiException as e:
            if e.status == 409:  # Already exists
                v1.patch_namespaced_service(name=f"{name}-service", namespace=namespace, body=service)
                logger.info(f"Updated service {name}-service in namespace {namespace}")
            else:
                raise

    async def create_pdb(self, name: str, namespace: str, spec: Dict[str, Any]) -> None:
        """Create Pod Disruption Budget for WebApp"""
        min_available = max(1, spec['replicas'] // 2)  # At least 50% available
        
        pdb = client.V1PodDisruptionBudget(
            metadata=client.V1ObjectMeta(
                name=f"{name}-pdb",
                namespace=namespace,
                labels={"app": name}
            ),
            spec=client.V1PodDisruptionBudgetSpec(
                min_available=min_available,
                selector=client.V1LabelSelector(
                    match_labels={"app": name}
                )
            )
        )

        try:
            policy_v1.create_namespaced_pod_disruption_budget(namespace=namespace, body=pdb)
            logger.info(f"Created PDB {name}-pdb with minAvailable: {min_available}")
        except client.exceptions.ApiException as e:
            if e.status == 409:  # Already exists
                policy_v1.patch_namespaced_pod_disruption_budget(name=f"{name}-pdb", namespace=namespace, body=pdb)
                logger.info(f"Updated PDB {name}-pdb")
            else:
                raise

# Initialize operator
operator = WebAppOperator()

@kopf.on.create('platform.devops', 'v1', 'webapps')
async def create_webapp(spec, name, namespace, **kwargs):
    """Handle WebApp creation"""
    with RECONCILE_DURATION.time():
        logger.info(f"Creating WebApp {name} in namespace {namespace}")
        
        await operator.create_deployment(name, namespace, spec)
        await operator.create_service(name, namespace, spec)
        await operator.create_pdb(name, namespace, spec)
        
        WEBAPP_CREATED.inc()
        WEBAPP_CURRENT.inc()
        WEBAPP_RECONCILED.inc()
        
        return {"phase": "Created", "message": f"WebApp {name} created successfully"}

@kopf.on.update('platform.devops', 'v1', 'webapps')
async def update_webapp(spec, name, namespace, **kwargs):
    """Handle WebApp updates"""
    with RECONCILE_DURATION.time():
        logger.info(f"Updating WebApp {name} in namespace {namespace}")
        
        await operator.create_deployment(name, namespace, spec)
        await operator.create_service(name, namespace, spec)
        await operator.create_pdb(name, namespace, spec)
        
        WEBAPP_RECONCILED.inc()
        
        return {"phase": "Updated", "message": f"WebApp {name} updated successfully"}

@kopf.on.delete('platform.devops', 'v1', 'webapps')
async def delete_webapp(name, namespace, **kwargs):
    """Handle WebApp deletion"""
    logger.info(f"Deleting WebApp {name} in namespace {namespace}")
    
    try:
        # Delete deployment
        apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
        # Delete service
        v1.delete_namespaced_service(name=f"{name}-service", namespace=namespace)
        # Delete PDB
        policy_v1.delete_namespaced_pod_disruption_budget(name=f"{name}-pdb", namespace=namespace)
        
        WEBAPP_DELETED.inc()
        WEBAPP_CURRENT.dec()
        
        logger.info(f"Successfully deleted WebApp {name}")
    except client.exceptions.ApiException as e:
        logger.error(f"Error deleting WebApp {name}: {e}")

if __name__ == "__main__":
    kopf.run()
