#!/usr/bin/env python3
"""Data versioning with DVC patterns"""

import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

class DataVersioner:
    def __init__(self, storage_path='/tmp/dvc_storage'):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.versions_path = self.storage_path / 'versions.json'
        self.versions = self._load_versions()
        
    def _load_versions(self):
        """Load version history"""
        if self.versions_path.exists():
            with open(self.versions_path, 'r') as f:
                return json.load(f)
        return []
    
    def _save_versions(self):
        """Save version history"""
        with open(self.versions_path, 'w') as f:
            json.dump(self.versions, f, indent=2)
    
    def _compute_hash(self, file_path):
        """Compute file hash"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def commit_dataset(self, data_path, message='', metadata=None):
        """Version a dataset"""
        data_path = Path(data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        # Compute hash
        file_hash = self._compute_hash(data_path)
        
        # Check if version already exists
        existing = next((v for v in self.versions if v['hash'] == file_hash), None)
        if existing:
            print(f"Dataset already versioned: {existing['version']}")
            return existing
        
        # Create new version
        version_num = len(self.versions) + 1
        version_id = f"v{version_num}"
        
        # Copy to storage
        storage_file = self.storage_path / f"{version_id}_{data_path.name}"
        shutil.copy2(data_path, storage_file)
        
        # Get file size
        file_size = data_path.stat().st_size / (1024 * 1024)  # MB
        
        version_info = {
            'version': version_id,
            'hash': file_hash,
            'filename': data_path.name,
            'storage_path': str(storage_file),
            'size_mb': round(file_size, 2),
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.versions.append(version_info)
        self._save_versions()
        
        print(f"Dataset versioned: {version_id}")
        print(f"Hash: {file_hash[:12]}...")
        print(f"Size: {file_size:.2f} MB")
        
        return version_info
    
    def get_version(self, version_id):
        """Get specific version"""
        return next((v for v in self.versions if v['version'] == version_id), None)
    
    def list_versions(self):
        """List all versions"""
        print(f"\nDataset Versions ({len(self.versions)} total):")
        print("-" * 80)
        for v in self.versions:
            print(f"{v['version']}: {v['filename']} ({v['size_mb']} MB) - {v['message']}")
            print(f"  Hash: {v['hash'][:12]}... | {v['timestamp']}")
        print("-" * 80)
        
    def checkout_version(self, version_id, output_path):
        """Checkout specific version"""
        version = self.get_version(version_id)
        if not version:
            raise ValueError(f"Version not found: {version_id}")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(version['storage_path'], output_path)
        print(f"Checked out {version_id} to {output_path}")
        
        return output_path

if __name__ == '__main__':
    versioner = DataVersioner()
    
    # Version latest dataset
    data_path = Path('/tmp/pipeline_data/feature_store/latest.parquet')
    if data_path.exists():
        versioner.commit_dataset(
            data_path,
            message='Feature engineering with user aggregations',
            metadata={'features': 15, 'records': 1000}
        )
    
    versioner.list_versions()
