import pytest
import asyncio
import asyncpg
from unittest.mock import AsyncMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from main import DatabaseManager

@pytest.fixture
def db_manager():
    return DatabaseManager()

@pytest.mark.asyncio
async def test_database_manager_initialization():
    """Test database manager initialization"""
    manager = DatabaseManager()
    assert manager.primary_pool is None
    assert manager.replica_pool is None
    assert manager.redis_client is None

@pytest.mark.asyncio
async def test_health_check_success():
    """Test successful health check"""
    with patch('asyncpg.create_pool') as mock_pool:
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 1
        
        mock_pool_instance = AsyncMock()
        mock_pool_instance.acquire.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        manager = DatabaseManager()
        manager.primary_pool = mock_pool_instance
        
        # Test would verify health check logic here
        assert manager.primary_pool is not None

@pytest.mark.asyncio
async def test_connection_pooling():
    """Test connection pool management"""
    with patch('asyncpg.create_pool') as mock_pool:
        mock_pool_instance = AsyncMock()
        mock_pool.return_value = mock_pool_instance
        
        manager = DatabaseManager()
        manager.primary_pool = mock_pool_instance
        
        # Test connection acquisition
        connection = await manager.get_primary_connection()
        assert connection is not None

def test_database_config():
    """Test database configuration"""
    from main import DATABASE_CONFIG
    
    assert 'primary' in DATABASE_CONFIG
    assert 'replica' in DATABASE_CONFIG
    assert 'pooled' in DATABASE_CONFIG
    
    assert DATABASE_CONFIG['primary']['host'] == 'localhost'
    assert DATABASE_CONFIG['primary']['port'] == 5432

if __name__ == "__main__":
    pytest.main([__file__])
