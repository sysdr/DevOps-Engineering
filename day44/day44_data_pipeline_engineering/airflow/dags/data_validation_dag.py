from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import json
from pathlib import Path

default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

def run_validation(**context):
    """Run data validation checks"""
    print("Running data validation...")
    
    # Load latest data from feature store
    data_path = Path('/tmp/pipeline_data/feature_store/latest.parquet')
    if not data_path.exists():
        print("No data to validate")
        return {'status': 'skipped', 'reason': 'no_data'}
    
    df = pd.read_parquet(data_path)
    
    # Validation rules
    validations = {
        'not_null_user_id': df['user_id'].notna().all(),
        'age_range': ((df['age'] >= 13) & (df['age'] <= 120)).all(),
        'valid_event_types': df['event_type'].isin(['click', 'view', 'purchase']).all(),
        'positive_amounts': (df['amount'] > 0).all(),
        'recent_timestamps': (pd.to_datetime(df['timestamp']) <= datetime.now()).all(),
        'min_row_count': len(df) >= 100,
        'no_duplicate_users': df['user_id'].is_unique
    }
    
    # Calculate validation score
    passed_checks = sum(validations.values())
    total_checks = len(validations)
    validation_score = (passed_checks / total_checks) * 100
    
    results = {
        'validation_score': float(validation_score),
        'passed_checks': int(passed_checks),
        'total_checks': int(total_checks),
        'failures': [k for k, v in validations.items() if not v],
        'timestamp': datetime.now().isoformat(),
        'record_count': int(len(df))
    }
    
    # Save validation results
    results_path = Path('/tmp/pipeline_data/validation/results.json')
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Validation Score: {validation_score:.1f}%")
    print(f"Passed: {passed_checks}/{total_checks} checks")
    
    if validation_score < 90:
        print(f"WARNING: Validation score below threshold! Failures: {results['failures']}")
    
    return results

dag = DAG(
    'data_validation_dag',
    default_args=default_args,
    description='Validate data quality with Great Expectations patterns',
    schedule_interval='@hourly',
    catchup=False,
    tags=['validation', 'quality']
)

validation_task = PythonOperator(
    task_id='run_validation',
    python_callable=run_validation,
    dag=dag,
)
