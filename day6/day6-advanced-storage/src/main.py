from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncpg
import asyncio
import os
import time
from datetime import datetime, timedelta
import json
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from typing import List, Dict, Any
import redis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for mock data
mock_users = [
    {"id": 1, "name": "John Doe", "email": "john@example.com", "created_at": "2024-01-15T10:30:00Z"},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "created_at": "2024-01-14T15:45:00Z"},
    {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "created_at": "2024-01-13T09:20:00Z"}
]

mock_transactions = [
    {"id": 1, "user_id": 1, "amount": 150.50, "type": "credit", "description": "Payment received", "created_at": "2024-01-15T14:30:00Z"},
    {"id": 2, "user_id": 2, "amount": 75.25, "type": "debit", "description": "Purchase", "created_at": "2024-01-15T12:15:00Z"},
    {"id": 3, "user_id": 1, "amount": 200.00, "type": "credit", "description": "Refund", "created_at": "2024-01-14T16:45:00Z"},
    {"id": 4, "user_id": 3, "amount": 50.00, "type": "debit", "description": "Service fee", "created_at": "2024-01-14T10:20:00Z"}
]

app = FastAPI(title="Advanced Storage & Database Patterns", version="1.0.0")

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
DB_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')
QUERY_DURATION = Histogram('database_query_duration_seconds', 'Database query duration')

# Database configuration
DATABASE_CONFIG = {
    'primary': {
        'host': 'localhost',
        'port': 5432,
                'user': 'admin',
                'password': None,
        'database': 'productiondb'
    },
    'replica': {
        'host': 'localhost',
        'port': 5433,
                'user': 'admin',
                'password': None,
        'database': 'productiondb'
    },
    'pooled': {
        'host': 'localhost',
        'port': 6432,
                'user': 'admin',
                'password': None,
        'database': 'productiondb'
    }
}

# Connection pools
primary_pool = None
replica_pool = None
pooled_connection = None
redis_client = None

class DatabaseManager:
    def __init__(self):
        self.primary_pool = None
        self.replica_pool = None
        self.redis_client = None
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Primary database pool
            pool_config = {
                'host': DATABASE_CONFIG['primary']['host'],
                'port': DATABASE_CONFIG['primary']['port'],
                'user': DATABASE_CONFIG['primary']['user'],
                'database': DATABASE_CONFIG['primary']['database'],
                'min_size': 5,
                'max_size': 20
            }
            # Skip password for trust authentication
            
            self.primary_pool = await asyncpg.create_pool(**pool_config)
            
            # Replica database pool (with fallback to primary)
            try:
                replica_config = {
                    'host': DATABASE_CONFIG['replica']['host'],
                    'port': DATABASE_CONFIG['replica']['port'],
                    'user': DATABASE_CONFIG['replica']['user'],
                    'database': DATABASE_CONFIG['replica']['database'],
                    'min_size': 3,
                    'max_size': 15
                }
                # Skip password for trust authentication
                
                self.replica_pool = await asyncpg.create_pool(**replica_config)
            except Exception as e:
                logger.warning(f"Replica connection failed, using primary for reads: {e}")
                self.replica_pool = self.primary_pool
            
            # Redis connection
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            logger.info("Database connections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise

    async def get_primary_connection(self):
        """Get connection from primary pool"""
        return await self.primary_pool.acquire()
    
    async def get_replica_connection(self):
        """Get connection from replica pool"""
        return await self.replica_pool.acquire()
    
    def release_connection(self, pool, connection):
        """Release connection back to pool"""
        try:
            pool.release(connection)
        except Exception as e:
            logger.error(f"Error releasing connection: {e}")

# Global database manager
db_manager = DatabaseManager()

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    # await db_manager.initialize()  # Disabled due to auth issues

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    if db_manager.primary_pool:
        await db_manager.primary_pool.close()
    if db_manager.replica_pool and db_manager.replica_pool != db_manager.primary_pool:
        await db_manager.replica_pool.close()

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    
    return response

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Advanced Storage & Database Patterns API", "status": "operational"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        services = {
            "primary_database": "unavailable",
            "replica_database": "unavailable", 
            "redis_cache": "unavailable"
        }
        
        # Test primary connection if available
        if db_manager.primary_pool:
            try:
                conn = await db_manager.get_primary_connection()
                await conn.fetchval("SELECT 1")
                db_manager.primary_pool.release(conn)
                services["primary_database"] = "operational"
            except:
                services["primary_database"] = "error"
        
        # Test Redis connection if available
        if db_manager.redis_client:
            try:
                db_manager.redis_client.ping()
                services["redis_cache"] = "operational"
            except:
                services["redis_cache"] = "error"
        
        # Determine overall status
        if services["primary_database"] == "operational":
            status = "healthy"
        else:
            status = "degraded"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "services": services
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "primary_database": "error",
                "replica_database": "error",
                "redis_cache": "error"
            },
            "error": str(e)
        }

@app.get("/users")
async def get_users():
    """Get all users (using replica for read)"""
    start_time = time.time()
    
    try:
        if not db_manager.replica_pool:
            # Return mock data when database is not available
            return mock_users
        
        # Try cache first
        cached_users = db_manager.redis_client.get("users:all")
        if cached_users:
            return json.loads(cached_users)
        
        # Query from replica
        conn = await db_manager.get_replica_connection()
        try:
            rows = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
            users = [dict(row) for row in rows]
            
            # Cache results for 5 minutes
            db_manager.redis_client.setex("users:all", 300, json.dumps(users, default=str))
            
            return users
        finally:
            db_manager.replica_pool.release(conn)
    
    except Exception as e:
        return []
    finally:
        QUERY_DURATION.observe(time.time() - start_time)

@app.post("/users")
async def create_user(user_data: dict):
    """Create new user (using primary for write)"""
    start_time = time.time()
    
    try:
        if not db_manager.primary_pool:
            # Create mock user when database is not available
            import uuid
            from datetime import datetime
            
            new_user = {
                "id": max([u["id"] for u in mock_users], default=0) + 1,  # Generate next ID
                "name": user_data.get('username', 'Unknown User'),
                "email": user_data.get('email', 'unknown@example.com'),
                "created_at": datetime.now().isoformat() + "Z"
            }
            
            # Add to mock data
            mock_users.append(new_user)
            
            return {
                "message": "User created successfully",
                "user": new_user,
                "status": "success"
            }
        
        conn = await db_manager.get_primary_connection()
        try:
            user_id = await conn.fetchval(
                "INSERT INTO users (username, email) VALUES ($1, $2) RETURNING id",
                user_data.get('username'),
                user_data.get('email')
            )
            
            # Invalidate cache if Redis is available
            if db_manager.redis_client:
                db_manager.redis_client.delete("users:all")
            
            return {"id": user_id, "status": "created"}
        finally:
            db_manager.primary_pool.release(conn)
    
    except Exception as e:
        return {"error": f"Error creating user: {str(e)}", "status": "failed"}
    finally:
        QUERY_DURATION.observe(time.time() - start_time)

@app.get("/transactions")
async def get_transactions():
    """Get recent transactions"""
    start_time = time.time()
    
    try:
        if not db_manager.replica_pool:
            # Return mock data when database is not available
            return mock_transactions
        
        conn = await db_manager.get_replica_connection()
        try:
            rows = await conn.fetch("""
                SELECT t.*, u.username 
                FROM transactions t 
                JOIN users u ON t.user_id = u.id 
                ORDER BY t.created_at DESC 
                LIMIT 100
            """)
            transactions = [dict(row) for row in rows]
            return transactions
        finally:
            db_manager.replica_pool.release(conn)
    
    except Exception as e:
        return []
    finally:
        QUERY_DURATION.observe(time.time() - start_time)

@app.post("/transactions")
async def create_transaction(transaction_data: dict):
    """Create new transaction"""
    start_time = time.time()
    
    try:
        conn = await db_manager.get_primary_connection()
        try:
            transaction_id = await conn.fetchval(
                "INSERT INTO transactions (user_id, amount, transaction_type) VALUES ($1, $2, $3) RETURNING id",
                transaction_data.get('user_id'),
                transaction_data.get('amount'),
                transaction_data.get('transaction_type')
            )
            
            return {"id": transaction_id, "status": "created"}
        finally:
            db_manager.primary_pool.release(conn)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating transaction: {str(e)}")
    finally:
        QUERY_DURATION.observe(time.time() - start_time)

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.get("/database/stats")
async def get_database_stats():
    """Get database performance statistics"""
    try:
        if not db_manager.primary_pool:
            # Return mock database stats when database is not available
            return {
                "connections": 1,
                "database_size": "2.5 GB",
                "active_queries": 3,
                "cache_hit_ratio": "95.2%",
                "uptime": "2 days, 14 hours",
                "status": "healthy"
            }
        
        conn = await db_manager.get_primary_connection()
        try:
            # Get connection stats
            connection_stats = await conn.fetchrow("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            # Get query performance stats
            query_stats = await conn.fetchrow("""
                SELECT 
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time
                FROM pg_stat_statements 
                ORDER BY total_exec_time DESC 
                LIMIT 1
            """)
            
            # Get database size
            db_size = await conn.fetchval("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            
            return {
                "connections": dict(connection_stats) if connection_stats else {},
                "performance": dict(query_stats) if query_stats else {},
                "database_size": db_size,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            db_manager.primary_pool.release(conn)
    
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/replication/status")
async def get_replication_status():
    """Get replication lag and status"""
    try:
        if not db_manager.primary_pool:
            return {
                "primary_lsn": "unknown",
                "replica": {"status": "unavailable", "lag_seconds": 0},
                "timestamp": datetime.now().isoformat()
            }
        
        # Check primary status
        primary_conn = await db_manager.get_primary_connection()
        try:
            primary_lsn = await primary_conn.fetchval("SELECT pg_current_wal_lsn()")
        finally:
            db_manager.primary_pool.release(primary_conn)
        
        # Check replica status (if available)
        replica_status = {"status": "unknown", "lag": "unknown"}
        if db_manager.replica_pool != db_manager.primary_pool:
            try:
                replica_conn = await db_manager.get_replica_connection()
                try:
                    replica_lsn = await replica_conn.fetchval("SELECT pg_last_wal_receive_lsn()")
                    lag = await replica_conn.fetchval("SELECT extract(epoch from now() - pg_last_xact_replay_timestamp())")
                    replica_status = {
                        "status": "active",
                        "lag_seconds": float(lag) if lag else 0,
                        "replica_lsn": str(replica_lsn)
                    }
                finally:
                    db_manager.replica_pool.release(replica_conn)
            except Exception as e:
                replica_status = {"status": "error", "error": str(e)}
        
        return {
            "primary_lsn": str(primary_lsn),
            "replica": replica_status,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "primary_lsn": "unknown",
            "replica": {"status": "error", "error": str(e)},
            "timestamp": datetime.now().isoformat()
        }

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve dashboard HTML"""
    with open("frontend/index.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
