import asyncio
import asyncpg
import subprocess
import os
import boto3
import schedule
import time
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'appuser',
            'password': '',
            'database': 'productiondb'
        }
        self.backup_dir = '/tmp/backups'
        os.makedirs(self.backup_dir, exist_ok=True)

    async def create_logical_backup(self):
        """Create logical backup using pg_dump"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{self.backup_dir}/logical_backup_{timestamp}.sql"
        
        try:
            # Create pg_dump backup using Docker
            cmd = [
                'docker', 'exec', 'postgres-primary',
                'pg_dump', '-U', self.db_config['user'], 
                '-d', self.db_config['database'], '--no-password'
            ]
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                logger.info(f"Logical backup created: {backup_file}")
                
                # Compress backup
                compressed_file = f"{backup_file}.gz"
                subprocess.run(['gzip', backup_file])
                
                return compressed_file
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating logical backup: {e}")
            return None

    async def create_wal_backup(self):
        """Archive WAL files for point-in-time recovery"""
        try:
            # Use Docker to execute WAL commands
            cmd = [
                'docker', 'exec', 'postgres-primary',
                'psql', '-U', self.db_config['user'], 
                '-d', self.db_config['database'], '-t', '-c',
                'SELECT pg_switch_wal(); SELECT pg_current_wal_lsn();'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"WAL backup failed: {result.stderr}")
                return None
                
            lines = result.stdout.strip().split('\n')
            current_lsn = lines[-1].strip() if lines else "unknown"
            
            logger.info(f"WAL backup point created at LSN: {current_lsn}")
            return current_lsn
            
        except Exception as e:
            logger.error(f"Error creating WAL backup: {e}")
            return None

    async def test_backup_restore(self, backup_file):
        """Test backup restoration procedure"""
        test_db = 'test_restore_db'
        
        try:
            # Create test database
            conn = await asyncpg.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database='postgres'  # Connect to default database
            )
            
            try:
                await conn.execute(f"DROP DATABASE IF EXISTS {test_db}")
                await conn.execute(f"CREATE DATABASE {test_db}")
            finally:
                await conn.close()
            
            # Restore backup to test database
            if backup_file.endswith('.gz'):
                cmd = f"gunzip -c {backup_file} | psql postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{test_db}"
            else:
                cmd = f"psql postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{test_db} < {backup_file}"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Verify restoration
                test_conn = await asyncpg.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database=test_db
                )
                
                user_count = await test_conn.fetchval("SELECT COUNT(*) FROM users")
                transaction_count = await test_conn.fetchval("SELECT COUNT(*) FROM transactions")
                
                await test_conn.close()
                
                logger.info(f"Backup restoration test successful. Users: {user_count}, Transactions: {transaction_count}")
                
                # Cleanup test database
                cleanup_conn = await asyncpg.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database='postgres'
                )
                await cleanup_conn.execute(f"DROP DATABASE {test_db}")
                await cleanup_conn.close()
                
                return True
            else:
                logger.error(f"Backup restoration test failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing backup restore: {e}")
            return False

    async def cleanup_old_backups(self, retention_days=30):
        """Remove backups older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        logger.info(f"Removed old backup: {filename}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")

    async def get_backup_status(self):
        """Get current backup status and metrics"""
        try:
            backups = []
            total_size = 0
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    backups.append({
                        'filename': filename,
                        'size_bytes': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
                    total_size += stat.st_size
            
            return {
                'total_backups': len(backups),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'backups': sorted(backups, key=lambda x: x['created_at'], reverse=True)
            }
            
        except Exception as e:
            logger.error(f"Error getting backup status: {e}")
            return {'error': str(e)}

async def main():
    """Main backup routine"""
    manager = BackupManager()
    
    # Create logical backup
    backup_file = await manager.create_logical_backup()
    
    if backup_file:
        # Test the backup
        test_result = await manager.test_backup_restore(backup_file)
        logger.info(f"Backup test result: {'PASSED' if test_result else 'FAILED'}")
    
    # Create WAL backup point
    await manager.create_wal_backup()
    
    # Cleanup old backups
    await manager.cleanup_old_backups()
    
    # Get status
    status = await manager.get_backup_status()
    logger.info(f"Backup status: {json.dumps(status, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
