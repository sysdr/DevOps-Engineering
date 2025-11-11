from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yaml
import os
from datetime import datetime

app = FastAPI(title="Crossplane Infrastructure API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class InfrastructureRequest(BaseModel):
    name: str
    type: str  # database, storage, compute
    size: str  # small, medium, large
    cloud: str  # aws, gcp
    namespace: str = "default"
    backup_enabled: bool = True

class InfrastructureStatus(BaseModel):
    name: str
    type: str
    status: str
    ready: bool
    cloud: str
    created_at: Optional[str]
    conditions: List[Dict[str, Any]]

# Initialize Kubernetes client
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
api_client = None
custom_api = None
core_api = None

# In-memory store for demo resources (when Kubernetes is unavailable)
demo_resources_store = []

try:
    config.load_incluster_config()
    api_client = client.ApiClient()
    custom_api = client.CustomObjectsApi(api_client)
    core_api = client.CoreV1Api(api_client)
    DEMO_MODE = False
except:
    try:
        config.load_kube_config()
        api_client = client.ApiClient()
        custom_api = client.CustomObjectsApi(api_client)
        core_api = client.CoreV1Api(api_client)
        DEMO_MODE = False
    except:
        DEMO_MODE = True
        print("Warning: Kubernetes not available, running in DEMO_MODE")

@app.get("/")
def root():
    return {
        "service": "Crossplane Infrastructure API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    if DEMO_MODE:
        return {"status": "healthy", "crossplane": "demo_mode"}
    try:
        core_api.list_namespace()
        return {"status": "healthy", "crossplane": "connected"}
    except Exception as e:
        return {"status": "healthy", "crossplane": "demo_mode", "note": str(e)}

@app.post("/infrastructure/provision")
async def provision_infrastructure(request: InfrastructureRequest):
    """Provision infrastructure using Crossplane composite resources"""
    
    # Store in demo resources if in DEMO_MODE
    if DEMO_MODE:
        new_resource = {
            "name": request.name,
            "type": request.type,
            "status": "Provisioning",
            "ready": False,
            "cloud": request.cloud,
            "created_at": datetime.now().isoformat(),
            "namespace": request.namespace
        }
        demo_resources_store.append(new_resource)
        return {
            "status": "provisioning",
            "name": request.name,
            "type": request.type,
            "cloud": request.cloud,
            "demo": True,
            "message": "Demo mode: Resource added to demo store"
        }
    
    if request.type not in ["database", "storage"]:
        raise HTTPException(status_code=400, detail=f"Unsupported type: {request.type}")
    
    if request.type == "database":
        resource = create_database_claim(request)
    elif request.type == "storage":
        resource = create_storage_claim(request)
    
    try:
        result = custom_api.create_namespaced_custom_object(
            group="platform.example.com",
            version="v1alpha1",
            namespace=request.namespace,
            plural=f"{request.type}s",
            body=resource
        )
        return {
            "status": "provisioning",
            "name": request.name,
            "type": request.type,
            "cloud": request.cloud,
            "resource": result
        }
    except Exception as e:
        # Store in demo resources if Kubernetes connection fails
        new_resource = {
            "name": request.name,
            "type": request.type,
            "status": "Provisioning",
            "ready": False,
            "cloud": request.cloud,
            "created_at": datetime.now().isoformat(),
            "namespace": request.namespace
        }
        demo_resources_store.append(new_resource)
        
        # Return demo response
        return {
            "status": "provisioning",
            "name": request.name,
            "type": request.type,
            "cloud": request.cloud,
            "demo": True,
            "message": f"Demo mode: Resource added to demo store - {str(e)}"
        }

@app.get("/infrastructure/status/{namespace}/{name}")
async def get_infrastructure_status(namespace: str, name: str):
    """Get status of provisioned infrastructure"""
    
    try:
        # Try to find the resource across different types
        for resource_type in ["databases", "storages"]:
            try:
                resource = custom_api.get_namespaced_custom_object(
                    group="platform.example.com",
                    version="v1alpha1",
                    namespace=namespace,
                    plural=resource_type,
                    name=name
                )
                
                status = resource.get("status", {})
                conditions = status.get("conditions", [])
                
                ready = False
                for condition in conditions:
                    if condition.get("type") == "Ready" and condition.get("status") == "True":
                        ready = True
                        break
                
                return InfrastructureStatus(
                    name=name,
                    type=resource_type.rstrip('s'),
                    status=status.get("phase", "Unknown"),
                    ready=ready,
                    cloud=resource.get("spec", {}).get("cloud", "unknown"),
                    created_at=resource.get("metadata", {}).get("creationTimestamp"),
                    conditions=conditions
                )
            except:
                continue
        
        raise HTTPException(status_code=404, detail="Resource not found")
        
    except client.exceptions.ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/infrastructure/list/{namespace}")
async def list_infrastructure(namespace: str):
    """List all infrastructure resources"""
    
    # Start with demo resources from store (filtered by namespace)
    namespace_resources = [r for r in demo_resources_store if r.get("namespace", "default") == namespace]
    
    if DEMO_MODE:
        # Add some initial demo data if store is empty
        if not namespace_resources:
            initial_demo = [
                {
                    "name": "demo-database-prod",
                    "type": "database",
                    "status": "Ready",
                    "ready": True,
                    "cloud": "aws",
                    "created_at": (datetime.now()).isoformat(),
                    "namespace": namespace
                },
                {
                    "name": "demo-storage-backup",
                    "type": "storage",
                    "status": "Ready",
                    "ready": True,
                    "cloud": "aws",
                    "created_at": (datetime.now()).isoformat(),
                    "namespace": namespace
                }
            ]
            demo_resources_store.extend(initial_demo)
            namespace_resources = initial_demo
        
        return {"resources": namespace_resources, "count": len(namespace_resources), "demo": True}
    
    all_resources = []
    
    # Try to get resources from Kubernetes
    try:
        for resource_type in ["databases", "storages"]:
            try:
                resources = custom_api.list_namespaced_custom_object(
                    group="platform.example.com",
                    version="v1alpha1",
                    namespace=namespace,
                    plural=resource_type
                )
                
                for item in resources.get("items", []):
                    status = item.get("status", {})
                    conditions = status.get("conditions", [])
                    ready = any(c.get("type") == "Ready" and c.get("status") == "True" 
                              for c in conditions)
                    
                    all_resources.append({
                        "name": item["metadata"]["name"],
                        "type": resource_type.rstrip('s'),
                        "status": status.get("phase", "Unknown"),
                        "ready": ready,
                        "cloud": item.get("spec", {}).get("cloud", "unknown"),
                        "created_at": item["metadata"].get("creationTimestamp")
                    })
            except:
                continue
    except Exception as e:
        # If Kubernetes connection fails, just use demo resources
        pass
    
    # Always merge with demo resources
    all_resources.extend(namespace_resources)
    return {"resources": all_resources, "count": len(all_resources)}

@app.delete("/infrastructure/{namespace}/{name}")
async def delete_infrastructure(namespace: str, name: str):
    """Delete infrastructure resource"""
    
    # Try to delete from demo store first
    global demo_resources_store
    original_count = len(demo_resources_store)
    demo_resources_store = [r for r in demo_resources_store 
                           if not (r.get("name") == name and r.get("namespace", "default") == namespace)]
    deleted_from_store = len(demo_resources_store) < original_count
    
    if DEMO_MODE:
        if deleted_from_store:
            return {"status": "deleted", "name": name, "demo": True}
        return {"status": "deleting", "name": name, "demo": True, "message": "Resource not found in demo store"}
    
    for resource_type in ["databases", "storages"]:
        try:
            custom_api.delete_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=namespace,
                plural=resource_type,
                name=name
            )
            return {"status": "deleted", "name": name, "type": resource_type}
        except:
            continue
    
    # If not found in Kubernetes but was in demo store, return success
    if deleted_from_store:
        return {"status": "deleted", "name": name, "demo": True}
    
    raise HTTPException(status_code=404, detail="Resource not found")

@app.get("/providers/status")
async def get_providers_status():
    """Get status of Crossplane providers"""
    
    # Demo provider data
    demo_providers = [
        {
            "name": "provider-aws",
            "package": "xpkg.upbound.io/upbound/provider-aws",
            "healthy": True,
            "installed": True,
            "version": "v0.36.0"
        },
        {
            "name": "provider-gcp",
            "package": "xpkg.upbound.io/upbound/provider-gcp",
            "healthy": True,
            "installed": True,
            "version": "v0.33.0"
        }
    ]
    
    if DEMO_MODE:
        return {"providers": demo_providers, "count": len(demo_providers), "demo": True}
    
    try:
        providers = custom_api.list_cluster_custom_object(
            group="pkg.crossplane.io",
            version="v1",
            plural="providers"
        )
        
        provider_list = []
        for provider in providers.get("items", []):
            status = provider.get("status", {})
            conditions = status.get("conditions", [])
            
            healthy = any(c.get("type") == "Healthy" and c.get("status") == "True" 
                         for c in conditions)
            installed = any(c.get("type") == "Installed" and c.get("status") == "True" 
                          for c in conditions)
            
            provider_list.append({
                "name": provider["metadata"]["name"],
                "package": provider["spec"]["package"],
                "healthy": healthy,
                "installed": installed,
                "version": status.get("currentRevision", "unknown")
            })
        
        return {"providers": provider_list, "count": len(provider_list)}
    except Exception as e:
        # Return demo data if Kubernetes connection fails
        return {"providers": demo_providers, "count": len(demo_providers), "demo": True, "note": f"Kubernetes unavailable: {str(e)}"}

def create_database_claim(request: InfrastructureRequest) -> dict:
    """Create database claim resource"""
    return {
        "apiVersion": "platform.example.com/v1alpha1",
        "kind": "Database",
        "metadata": {
            "name": request.name,
            "labels": {
                "cloud": request.cloud,
                "size": request.size
            }
        },
        "spec": {
            "cloud": request.cloud,
            "size": request.size,
            "backupEnabled": request.backup_enabled,
            "compositionSelector": {
                "matchLabels": {
                    "cloud": request.cloud
                }
            },
            "writeConnectionSecretToRef": {
                "name": f"{request.name}-connection",
                "namespace": request.namespace
            }
        }
    }

def create_storage_claim(request: InfrastructureRequest) -> dict:
    """Create storage claim resource"""
    return {
        "apiVersion": "platform.example.com/v1alpha1",
        "kind": "Storage",
        "metadata": {
            "name": request.name,
            "labels": {
                "cloud": request.cloud,
                "size": request.size
            }
        },
        "spec": {
            "cloud": request.cloud,
            "size": request.size,
            "compositionSelector": {
                "matchLabels": {
                    "cloud": request.cloud
                }
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
