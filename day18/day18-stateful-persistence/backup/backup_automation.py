import asyncio
import subprocess
import boto3
import json
import logging
from datetime import datetime, timedelta
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupAutomation:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.backup_bucket = 'postgres-backups-day18'
        
    async def create_logical_backup(self):
        """Create logical backup using pg_dump"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"postgres_backup_{timestamp}.sql"
            
            # Connect to primary database
            conn = psycopg2.connect(
                host="postgres-primary",
                database="statefuldb",
                user="dbuser",
                password="secure123"
            )
            
            # Create backup
            cmd = [
                'pg_dump',
                '-h', 'postgres-primary',
                '-U', 'dbuser',
                '-d', 'statefuldb',
                '-f', backup_file,
                '--verbose'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Logical backup created: {backup_file}")
                await self.upload_to_s3(backup_file)
                await self.cleanup_old_backups()
            else:
                logger.error(f"Backup failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Logical backup failed: {e}")
    
    async def upload_to_s3(self, backup_file):
        """Upload backup to S3"""
        try:
            s3_key = f"logical-backups/{backup_file}"
            
            self.s3_client.upload_file(
                backup_file,
                self.backup_bucket,
                s3_key
            )
            
            logger.info(f"Backup uploaded to S3: s3://{self.backup_bucket}/{s3_key}")
            
            # Clean up local file
            subprocess.run(['rm', backup_file])
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
    
    async def cleanup_old_backups(self):
        """Remove backups older than 30 days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.backup_bucket,
                Prefix='logical-backups/'
            )
            
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    self.s3_client.delete_object(
                        Bucket=self.backup_bucket,
                        Key=obj['Key']
                    )
                    logger.info(f"Deleted old backup: {obj['Key']}")
                    
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def test_backup_restore(self):
        """Test backup and restore procedure"""
        try:
            # Create test database
            test_db = "test_restore_db"
            
            conn = psycopg2.connect(
                host="postgres-primary",
                database="postgres",
                user="dbuser",
                password="secure123"
            )
            conn.autocommit = True
            
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {test_db}")
            cursor.execute(f"CREATE DATABASE {test_db}")
            
            # Get latest backup
            response = self.s3_client.list_objects_v2(
                Bucket=self.backup_bucket,
                Prefix='logical-backups/',
                MaxKeys=1
            )
            
            if 'Contents' in response:
                latest_backup = response['Contents'][0]['Key']
                local_file = latest_backup.split('/')[-1]
                
                # Download backup
                self.s3_client.download_file(
                    self.backup_bucket,
                    latest_backup,
                    local_file
                )
                
                # Restore backup
                cmd = [
                    'psql',
                    '-h', 'postgres-primary',
                    '-U', 'dbuser',
                    '-d', test_db,
                    '-f', local_file
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("Backup restore test successful")
                else:
                    logger.error(f"Restore test failed: {result.stderr}")
                
                # Cleanup
                subprocess.run(['rm', local_file])
                cursor.execute(f"DROP DATABASE {test_db}")
                
        except Exception as e:
            logger.error(f"Restore test failed: {e}")

async def main():
    automation = BackupAutomation()
    await automation.create_logical_backup()
    await automation.test_backup_restore()

if __name__ == "__main__":
    asyncio.run(main())
