"""
Drift Detection System - Compares cluster state against Git manifests
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DriftResult:
    resource_name: str
    resource_kind: str
    namespace: str
    drift_detected: bool
    diff_summary: Optional[str]
    last_checked: str
    git_commit: Optional[str]
    remediation_action: Optional[str]


class ResourceNormalizer:
    """Normalize Kubernetes resources for comparison"""
    
    IGNORE_FIELDS = [
        'metadata.resourceVersion',
        'metadata.generation',
        'metadata.creationTimestamp',
        'metadata.uid',
        'metadata.selfLink',
        'metadata.managedFields',
        'status'
    ]
    
    @staticmethod
    def normalize(resource: Dict) -> Dict:
        """Remove fields that change on every reconciliation"""
        normalized = json.loads(json.dumps(resource))
        
        # Remove metadata fields
        if 'metadata' in normalized:
            for field in ['resourceVersion', 'generation', 'creationTimestamp', 
                         'uid', 'selfLink', 'managedFields']:
                normalized['metadata'].pop(field, None)
        
        # Remove status
        normalized.pop('status', None)
        
        # Sort for consistent comparison
        return normalized
    
    @staticmethod
    def compute_hash(resource: Dict) -> str:
        """Compute deterministic hash of normalized resource"""
        normalized = ResourceNormalizer.normalize(resource)
        resource_str = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(resource_str.encode()).hexdigest()


class DriftDetector:
    """Detects configuration drift between cluster and Git"""
    
    def __init__(self):
        self.git_manifests = {}
        self.cluster_state = {}
        self.drift_results = []
        
    async def load_git_manifests(self):
        """Simulate loading manifests from Git"""
        logger.info("Loading manifests from Git repository...")
        
        # Simulated Git manifests
        self.git_manifests = {
            'default/deployment/nginx': {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': 'nginx',
                    'namespace': 'default',
                    'labels': {'app': 'nginx'},
                    'annotations': {
                        'argocd.argoproj.io/sync-result': 'abc123'
                    }
                },
                'spec': {
                    'replicas': 3,
                    'selector': {'matchLabels': {'app': 'nginx'}},
                    'template': {
                        'metadata': {'labels': {'app': 'nginx'}},
                        'spec': {
                            'containers': [{
                                'name': 'nginx',
                                'image': 'nginx:1.21',
                                'ports': [{'containerPort': 80}]
                            }]
                        }
                    }
                }
            },
            'default/externalsecret/db-credentials': {
                'apiVersion': 'external-secrets.io/v1beta1',
                'kind': 'ExternalSecret',
                'metadata': {
                    'name': 'db-credentials',
                    'namespace': 'default',
                    'annotations': {'drift-policy': 'auto-remediate'}
                },
                'spec': {
                    'refreshInterval': '1h',
                    'secretStoreRef': {
                        'name': 'aws-secret-store',
                        'kind': 'SecretStore'
                    },
                    'target': {
                        'name': 'db-credentials',
                        'creationPolicy': 'Owner'
                    },
                    'data': [{
                        'secretKey': 'password',
                        'remoteRef': {'key': 'prod/db/password'}
                    }]
                }
            }
        }
        
    async def fetch_cluster_state(self):
        """Simulate fetching current cluster state"""
        logger.info("Fetching current cluster state...")
        
        # Simulate cluster state with drift in nginx deployment
        self.cluster_state = {
            'default/deployment/nginx': {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': 'nginx',
                    'namespace': 'default',
                    'labels': {'app': 'nginx'},
                    'annotations': {
                        'argocd.argoproj.io/sync-result': 'abc123'
                    },
                    'resourceVersion': '12345',
                    'generation': 3,
                    'creationTimestamp': '2025-05-20T10:00:00Z'
                },
                'spec': {
                    'replicas': 5,  # DRIFT: Should be 3 per Git
                    'selector': {'matchLabels': {'app': 'nginx'}},
                    'template': {
                        'metadata': {'labels': {'app': 'nginx'}},
                        'spec': {
                            'containers': [{
                                'name': 'nginx',
                                'image': 'nginx:1.21',
                                'ports': [{'containerPort': 80}]
                            }]
                        }
                    }
                },
                'status': {'readyReplicas': 5}
            },
            'default/externalsecret/db-credentials': {
                'apiVersion': 'external-secrets.io/v1beta1',
                'kind': 'ExternalSecret',
                'metadata': {
                    'name': 'db-credentials',
                    'namespace': 'default',
                    'annotations': {'drift-policy': 'auto-remediate'},
                    'resourceVersion': '67890'
                },
                'spec': {
                    'refreshInterval': '1h',
                    'secretStoreRef': {
                        'name': 'aws-secret-store',
                        'kind': 'SecretStore'
                    },
                    'target': {
                        'name': 'db-credentials',
                        'creationPolicy': 'Owner'
                    },
                    'data': [{
                        'secretKey': 'password',
                        'remoteRef': {'key': 'prod/db/password'}
                    }]
                }
            }
        }
    
    def detect_drift(self, resource_key: str) -> DriftResult:
        """Compare Git manifest with cluster state"""
        git_manifest = self.git_manifests.get(resource_key)
        cluster_resource = self.cluster_state.get(resource_key)
        
        if not git_manifest or not cluster_resource:
            return DriftResult(
                resource_name=resource_key.split('/')[-1],
                resource_kind=resource_key.split('/')[1],
                namespace=resource_key.split('/')[0],
                drift_detected=False,
                diff_summary="Resource not found",
                last_checked=datetime.utcnow().isoformat(),
                git_commit=None,
                remediation_action=None
            )
        
        git_hash = ResourceNormalizer.compute_hash(git_manifest)
        cluster_hash = ResourceNormalizer.compute_hash(cluster_resource)
        
        drift_detected = git_hash != cluster_hash
        diff_summary = None
        remediation_action = None
        
        if drift_detected:
            # Identify specific differences
            git_norm = ResourceNormalizer.normalize(git_manifest)
            cluster_norm = ResourceNormalizer.normalize(cluster_resource)
            
            diff_summary = self._compute_diff(git_norm, cluster_norm)
            
            # Check if auto-remediation is enabled
            annotations = cluster_resource.get('metadata', {}).get('annotations', {})
            if annotations.get('drift-policy') == 'auto-remediate':
                remediation_action = 'auto-remediate'
            else:
                remediation_action = 'alert-only'
        
        git_commit = git_manifest.get('metadata', {}).get('annotations', {}).get(
            'argocd.argoproj.io/sync-result', 'unknown'
        )
        
        return DriftResult(
            resource_name=resource_key.split('/')[-1],
            resource_kind=resource_key.split('/')[1],
            namespace=resource_key.split('/')[0],
            drift_detected=drift_detected,
            diff_summary=diff_summary,
            last_checked=datetime.utcnow().isoformat(),
            git_commit=git_commit,
            remediation_action=remediation_action
        )
    
    def _compute_diff(self, git_resource: Dict, cluster_resource: Dict) -> str:
        """Compute human-readable diff"""
        diffs = []
        
        # Check replicas (common drift point)
        git_replicas = git_resource.get('spec', {}).get('replicas')
        cluster_replicas = cluster_resource.get('spec', {}).get('replicas')
        
        if git_replicas != cluster_replicas:
            diffs.append(f"spec.replicas: git={git_replicas}, cluster={cluster_replicas}")
        
        # Check image (another common drift point)
        git_image = self._get_container_image(git_resource)
        cluster_image = self._get_container_image(cluster_resource)
        
        if git_image != cluster_image:
            diffs.append(f"container.image: git={git_image}, cluster={cluster_image}")
        
        return " | ".join(diffs) if diffs else "Unknown diff"
    
    def _get_container_image(self, resource: Dict) -> Optional[str]:
        """Extract container image from resource"""
        try:
            containers = resource['spec']['template']['spec']['containers']
            return containers[0]['image']
        except (KeyError, IndexError):
            return None
    
    async def run_drift_detection(self) -> List[DriftResult]:
        """Run full drift detection cycle"""
        logger.info("Starting drift detection cycle...")
        
        await self.load_git_manifests()
        await self.fetch_cluster_state()
        
        results = []
        for resource_key in self.git_manifests.keys():
            result = self.detect_drift(resource_key)
            results.append(result)
            
            if result.drift_detected:
                logger.warning(f"DRIFT DETECTED: {resource_key} - {result.diff_summary}")
                if result.remediation_action == 'auto-remediate':
                    logger.info(f"Auto-remediation enabled for {resource_key}")
            else:
                logger.info(f"No drift: {resource_key}")
        
        self.drift_results = results
        return results
    
    def get_drift_summary(self) -> Dict:
        """Get summary of drift detection results"""
        total = len(self.drift_results)
        drifted = sum(1 for r in self.drift_results if r.drift_detected)
        auto_remediate = sum(
            1 for r in self.drift_results 
            if r.drift_detected and r.remediation_action == 'auto-remediate'
        )
        
        return {
            'total_resources': total,
            'drifted_resources': drifted,
            'auto_remediation_enabled': auto_remediate,
            'drift_percentage': round((drifted / total * 100) if total > 0 else 0, 2),
            'last_scan': datetime.utcnow().isoformat()
        }


async def main():
    """Run drift detection demo"""
    detector = DriftDetector()
    results = await detector.run_drift_detection()
    summary = detector.get_drift_summary()
    
    print("\n" + "="*50)
    print("DRIFT DETECTION SUMMARY")
    print("="*50)
    print(json.dumps(summary, indent=2))
    
    print("\n" + "="*50)
    print("DETAILED RESULTS")
    print("="*50)
    for result in results:
        print(json.dumps(asdict(result), indent=2))


if __name__ == '__main__':
    asyncio.run(main())
