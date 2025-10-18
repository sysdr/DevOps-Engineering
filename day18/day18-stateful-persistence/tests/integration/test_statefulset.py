import pytest
import asyncio
import asyncpg
import subprocess
import time
import requests

class TestStatefulSetDeployment:
    
    @pytest.mark.asyncio
    async def test_primary_database_connection(self):
        """Test connection to primary database"""
        try:
            conn = await asyncpg.connect(
                host="postgres-primary",
                port=5432,
                database="statefuldb", 
                user="dbuser",
                password="secure123"
            )
            
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            assert result == 1
            
            await conn.close()
            
        except Exception as e:
            pytest.fail(f"Failed to connect to primary database: {e}")
    
    @pytest.mark.asyncio
    async def test_replica_database_connection(self):
        """Test connection to replica database"""
        try:
            conn = await asyncpg.connect(
                host="postgres-replica",
                port=5432,
                database="statefuldb",
                user="dbuser", 
                password="secure123"
            )
            
            # Test read-only query
            result = await conn.fetchval("SELECT version()")
            assert "PostgreSQL" in result
            
            await conn.close()
            
        except Exception as e:
            pytest.fail(f"Failed to connect to replica database: {e}")
    
    def test_statefulset_pods_running(self):
        """Test that all StatefulSet pods are running"""
        result = subprocess.run(
            ["kubectl", "get", "pods", "-l", "app=postgres", "-o", "jsonpath={.items[*].status.phase}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            phases = result.stdout.split()
            assert all(phase == "Running" for phase in phases), f"Not all pods running: {phases}"
        else:
            pytest.fail(f"Failed to get pod status: {result.stderr}")
    
    def test_persistent_volumes_bound(self):
        """Test that persistent volumes are properly bound"""
        result = subprocess.run(
            ["kubectl", "get", "pvc", "-l", "app=postgres", "-o", "jsonpath={.items[*].status.phase}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            phases = result.stdout.split()
            assert all(phase == "Bound" for phase in phases), f"Not all PVCs bound: {phases}"
        else:
            pytest.fail(f"Failed to get PVC status: {result.stderr}")
    
    @pytest.mark.asyncio
    async def test_data_persistence(self):
        """Test data persistence across pod restarts"""
        try:
            # Connect and insert test data
            conn = await asyncpg.connect(
                host="postgres-primary",
                port=5432,
                database="statefuldb",
                user="dbuser",
                password="secure123"
            )
            
            # Create test table and insert data
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS test_persistence (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            test_data = f"test_data_{int(time.time())}"
            await conn.execute(
                "INSERT INTO test_persistence (data) VALUES ($1)",
                test_data
            )
            
            await conn.close()
            
            # Restart primary pod
            subprocess.run(
                ["kubectl", "delete", "pod", "postgres-cluster-0"],
                check=True
            )
            
            # Wait for pod to restart
            time.sleep(30)
            
            # Reconnect and verify data
            conn = await asyncpg.connect(
                host="postgres-primary",
                port=5432,
                database="statefuldb",
                user="dbuser",
                password="secure123"
            )
            
            result = await conn.fetchval(
                "SELECT data FROM test_persistence WHERE data = $1",
                test_data
            )
            
            assert result == test_data, "Data not persisted across restart"
            
            await conn.close()
            
        except Exception as e:
            pytest.fail(f"Data persistence test failed: {e}")
    
    def test_monitoring_api_health(self):
        """Test monitoring API is responding"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            
        except requests.RequestException as e:
            pytest.fail(f"Monitoring API health check failed: {e}")
    
    def test_monitoring_cluster_metrics(self):
        """Test cluster metrics endpoint"""
        try:
            response = requests.get("http://localhost:8000/metrics/cluster", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert "primary" in data
            assert "replica" in data
            assert "cluster_health" in data
            
        except requests.RequestException as e:
            pytest.fail(f"Cluster metrics test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
