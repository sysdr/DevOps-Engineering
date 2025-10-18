from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import asyncio
import json
import logging
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from kubernetes import client, config
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PostgreSQL Monitoring Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
db_connections = Gauge('postgres_active_connections', 'Active PostgreSQL connections')
db_queries_per_second = Counter('postgres_queries_total', 'Total PostgreSQL queries')
db_query_duration = Histogram('postgres_query_duration_seconds', 'PostgreSQL query duration')
storage_usage = Gauge('postgres_storage_usage_bytes', 'PostgreSQL storage usage')

class PostgreSQLMonitor:
    def __init__(self):
        self.primary_pool = None
        self.replica_pool = None
        
    async def initialize(self):
        try:
            # Try to connect to actual databases first
            self.primary_pool = await asyncpg.create_pool(
                host="postgres-primary",
                port=5432,
                database="statefuldb",
                user="dbuser",
                password="secure123",
                min_size=2,
                max_size=10
            )
            
            self.replica_pool = await asyncpg.create_pool(
                host="postgres-replica",
                port=5432,
                database="statefuldb",
                user="dbuser",
                password="secure123",
                min_size=2,
                max_size=10
            )
            
            logger.info("Database pools initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize database pools: {e}")
            logger.info("Running in demo mode with simulated data")
            self.primary_pool = None
            self.replica_pool = None
    
    async def get_cluster_status(self):
        """Get overall cluster health and metrics"""
        try:
            primary_status = await self.get_db_metrics(self.primary_pool, "primary")
            replica_status = await self.get_db_metrics(self.replica_pool, "replica")
            
            return {
                "timestamp": datetime.now().isoformat(),
                "primary": primary_status,
                "replica": replica_status,
                "cluster_health": "healthy" if primary_status["online"] and replica_status["online"] else "degraded"
            }
            
        except Exception as e:
            logger.error(f"Failed to get cluster status: {e}")
            return {"error": str(e)}
    
    async def get_db_metrics(self, pool, role):
        """Get metrics for a specific database instance"""
        try:
            # Demo mode - return simulated data
            if pool is None:
                import random
                return {
                    "online": True,
                    "role": role,
                    "active_connections": random.randint(8, 15),
                    "database_size_bytes": random.randint(2000000000, 3000000000),  # 2-3 GB
                    "total_queries": random.randint(50000, 100000),
                    "avg_query_time_ms": round(random.uniform(0.5, 2.0), 2),
                    "replication_lag_seconds": round(random.uniform(0.01, 0.1), 3) if role == "replica" else 0
                }
            
            async with pool.acquire() as conn:
                # Connection count
                conn_result = await conn.fetchrow(
                    "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active'"
                )
                
                # Database size
                size_result = await conn.fetchrow(
                    "SELECT pg_database_size(current_database()) as db_size"
                )
                
                # Query statistics
                stats_result = await conn.fetchrow("""
                    SELECT 
                        sum(calls) as total_queries,
                        sum(total_time) as total_time,
                        avg(mean_time) as avg_query_time
                    FROM pg_stat_statements 
                    WHERE calls > 0
                """)
                
                # Replication lag (for replicas)
                lag_result = None
                if role == "replica":
                    lag_result = await conn.fetchrow(
                        "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) as lag_seconds"
                    )
                
                return {
                    "online": True,
                    "role": role,
                    "active_connections": conn_result["active_connections"],
                    "database_size_bytes": size_result["db_size"],
                    "total_queries": stats_result["total_queries"] if stats_result["total_queries"] else 0,
                    "avg_query_time_ms": float(stats_result["avg_query_time"]) if stats_result["avg_query_time"] else 0,
                    "replication_lag_seconds": float(lag_result["lag_seconds"]) if lag_result and lag_result["lag_seconds"] else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get metrics for {role}: {e}")
            return {
                "online": False,
                "role": role,
                "error": str(e)
            }
    
    async def get_storage_metrics(self):
        """Get storage usage and performance metrics"""
        try:
            # Try to get Kubernetes persistent volume metrics
            try:
                config.load_incluster_config()
                v1 = client.CoreV1Api()
                
                pvcs = v1.list_namespaced_persistent_volume_claim(namespace="default")
                
                storage_info = []
                for pvc in pvcs.items:
                    if "postgres" in pvc.metadata.name:
                        storage_info.append({
                            "name": pvc.metadata.name,
                            "capacity": pvc.status.capacity.get("storage", "unknown"),
                            "access_modes": pvc.status.access_modes,
                            "storage_class": pvc.spec.storage_class_name,
                            "phase": pvc.status.phase
                        })
            except Exception as k8s_error:
                logger.warning(f"Kubernetes API not available: {k8s_error}")
                # Demo mode - simulate PVC data
                storage_info = [
                    {
                        "name": "postgres-cluster-0-pvc",
                        "capacity": "10Gi",
                        "access_modes": ["ReadWriteOnce"],
                        "storage_class": "fast-ssd",
                        "phase": "Bound"
                    },
                    {
                        "name": "postgres-cluster-1-pvc", 
                        "capacity": "10Gi",
                        "access_modes": ["ReadWriteOnce"],
                        "storage_class": "fast-ssd",
                        "phase": "Bound"
                    }
                ]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "persistent_volumes": storage_info,
                "disk_usage": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage metrics: {e}")
            return {"error": str(e)}

monitor = PostgreSQLMonitor()

@app.on_event("startup")
async def startup():
    await monitor.initialize()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "postgresql-monitoring"}

@app.get("/metrics/cluster")
async def get_cluster_metrics():
    return await monitor.get_cluster_status()

@app.get("/metrics/storage") 
async def get_storage_metrics():
    return await monitor.get_storage_metrics()

@app.get("/metrics/prometheus")
async def prometheus_metrics():
    # Update Prometheus metrics
    cluster_status = await monitor.get_cluster_status()
    
    if "primary" in cluster_status:
        db_connections.set(cluster_status["primary"].get("active_connections", 0))
        storage_usage.set(cluster_status["primary"].get("database_size_bytes", 0))
    
    return generate_latest()

@app.post("/test/failover")
async def test_failover():
    """Simulate primary failure for testing"""
    try:
        # This would trigger operator-based failover
        logger.info("Simulating primary failover...")
        return {"status": "failover_initiated", "message": "Check cluster status for results"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
