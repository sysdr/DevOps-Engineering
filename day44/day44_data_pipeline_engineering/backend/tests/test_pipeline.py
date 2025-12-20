import pytest
import pandas as pd
import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent

# Load validation module directly
validation_path = project_root / 'validation' / 'ge_validator.py'
spec = importlib.util.spec_from_file_location("ge_validator", validation_path)
ge_validator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ge_validator_module)
DataValidator = ge_validator_module.DataValidator

# Load dvc version_data module directly (avoiding conflict with installed dvc package)
dvc_path = project_root / 'dvc' / 'version_data.py'
spec = importlib.util.spec_from_file_location("version_data", dvc_path)
version_data_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version_data_module)
DataVersioner = version_data_module.DataVersioner

@pytest.fixture
def sample_dataframe():
    """Create sample dataframe for testing"""
    data = {
        'user_id': [f'user_{i}' for i in range(100)],
        'age': [20 + (i % 50) for i in range(100)],
        'event_type': ['click' if i % 3 == 0 else 'view' for i in range(100)],
        'timestamp': pd.date_range('2025-01-01', periods=100, freq='H'),
        'amount': [10.5 + i for i in range(100)]
    }
    return pd.DataFrame(data)

def test_data_validator_initialization():
    """Test data validator initialization"""
    validator = DataValidator()
    assert len(validator.expectations) > 0
    assert 'user_id_not_null' in validator.expectations

def test_data_validation_passes(sample_dataframe):
    """Test validation with good data"""
    validator = DataValidator()
    result = validator.validate(sample_dataframe)
    
    assert result['validation_score'] > 80
    assert result['passed_expectations'] > 0
    assert 'dataset_info' in result

def test_data_validation_catches_nulls():
    """Test validation catches null values"""
    validator = DataValidator()
    
    # Create dataframe with nulls
    data = {
        'user_id': [None, 'user_2', 'user_3'],
        'age': [25, 30, 35],
        'event_type': ['click', 'view', 'click'],
        'timestamp': pd.date_range('2025-01-01', periods=3, freq='H'),
        'amount': [10.5, 20.0, 30.0]
    }
    df = pd.DataFrame(data)
    
    result = validator.validate(df)
    assert not result['results']['user_id_not_null']['passed']

def test_data_versioner_initialization():
    """Test data versioner initialization"""
    versioner = DataVersioner('/tmp/test_dvc_storage')
    assert versioner.storage_path.exists()

def test_data_versioning(sample_dataframe, tmp_path):
    """Test dataset versioning"""
    versioner = DataVersioner(tmp_path / 'dvc_storage')
    
    # Save sample dataframe
    data_file = tmp_path / 'test_data.parquet'
    sample_dataframe.to_parquet(data_file, index=False)
    
    # Version the dataset
    version = versioner.commit_dataset(
        data_file,
        message='Test dataset',
        metadata={'records': len(sample_dataframe)}
    )
    
    assert version['version'] == 'v1'
    assert 'hash' in version
    assert version['size_mb'] > 0

def test_data_versioning_duplicate_detection(sample_dataframe, tmp_path):
    """Test that duplicate datasets are detected"""
    versioner = DataVersioner(tmp_path / 'dvc_storage')
    
    # Save sample dataframe
    data_file = tmp_path / 'test_data.parquet'
    sample_dataframe.to_parquet(data_file, index=False)
    
    # Version twice
    version1 = versioner.commit_dataset(data_file, message='Version 1')
    version2 = versioner.commit_dataset(data_file, message='Version 2')
    
    assert version1['hash'] == version2['hash']
    assert len(versioner.versions) == 1  # Should not create duplicate

def test_pipeline_integration(sample_dataframe, tmp_path):
    """Test full pipeline integration"""
    # Save dataframe
    data_file = tmp_path / 'pipeline_data.parquet'
    sample_dataframe.to_parquet(data_file, index=False)
    
    # Validate
    validator = DataValidator()
    validation_result = validator.validate(sample_dataframe)
    assert validation_result['validation_score'] > 80
    
    # Version
    versioner = DataVersioner(tmp_path / 'dvc_storage')
    version = versioner.commit_dataset(data_file, message='Integration test')
    assert version['version'] == 'v1'
    
    # Checkout
    checkout_path = tmp_path / 'checkout.parquet'
    versioner.checkout_version('v1', checkout_path)
    assert checkout_path.exists()
    
    # Verify data integrity
    checked_out_df = pd.read_parquet(checkout_path)
    pd.testing.assert_frame_equal(sample_dataframe, checked_out_df)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
