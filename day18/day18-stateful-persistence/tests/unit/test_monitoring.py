import pytest
from unittest.mock import AsyncMock, patch
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/src'))

from monitoring_service import PostgreSQLMonitor

class TestPostgreSQLMonitor:
    
    @pytest.fixture
    def monitor(self):
        return PostgreSQLMonitor()
    
    @pytest.mark.asyncio
    async def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        with patch('asyncpg.create_pool') as mock_pool:
            mock_pool.side_effect = Exception("Connection failed")  # Force demo mode
            await monitor.initialize()
            # In demo mode, pools should be None
            assert monitor.primary_pool is None
            assert monitor.replica_pool is None
    
    @pytest.mark.asyncio
    async def test_get_db_metrics_demo_mode(self, monitor):
        """Test metrics collection in demo mode (no database connection)"""
        # Test demo mode behavior when pool is None
        result = await monitor.get_db_metrics(None, "replica")
        
        assert result["online"] == True
        assert result["role"] == "replica"
        assert "active_connections" in result
        assert "database_size_bytes" in result
        assert "total_queries" in result
        assert "avg_query_time_ms" in result
        assert "replication_lag_seconds" in result
        # In demo mode, replication lag should be > 0 for replica
        assert result["replication_lag_seconds"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_db_metrics_failure(self, monitor):
        """Test metrics collection failure handling"""
        mock_pool = AsyncMock()
        mock_pool.acquire.side_effect = Exception("Connection failed")
        
        result = await monitor.get_db_metrics(mock_pool, "primary")
        
        assert result["online"] == False
        assert result["role"] == "primary"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_cluster_status_healthy(self, monitor):
        """Test cluster status when all components healthy"""
        monitor.primary_pool = AsyncMock()
        monitor.replica_pool = AsyncMock()
        
        with patch.object(monitor, 'get_db_metrics') as mock_metrics:
            mock_metrics.side_effect = [
                {"online": True, "role": "primary"},
                {"online": True, "role": "replica"}
            ]
            
            result = await monitor.get_cluster_status()
            
            assert result["cluster_health"] == "healthy"
            assert "primary" in result
            assert "replica" in result
    
    @pytest.mark.asyncio 
    async def test_cluster_status_degraded(self, monitor):
        """Test cluster status when replica is down"""
        monitor.primary_pool = AsyncMock()
        monitor.replica_pool = AsyncMock()
        
        with patch.object(monitor, 'get_db_metrics') as mock_metrics:
            mock_metrics.side_effect = [
                {"online": True, "role": "primary"},
                {"online": False, "role": "replica"}
            ]
            
            result = await monitor.get_cluster_status()
            
            assert result["cluster_health"] == "degraded"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
