from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def extract_data(**context):
    """Extract data from source (simulated database)"""
    print("Extracting data from source...")
    
    # Simulate user events data
    data = {
        'user_id': range(1, 1001),
        'age': [20 + (i % 50) for i in range(1000)],
        'event_type': ['click' if i % 3 == 0 else 'view' if i % 3 == 1 else 'purchase' for i in range(1000)],
        'timestamp': [datetime.now() - timedelta(hours=i) for i in range(1000)],
        'amount': [10.5 + (i % 100) for i in range(1000)],
        'location': [f"City_{i % 20}" for i in range(1000)]
    }
    
    df = pd.DataFrame(data)
    
    # Save raw data
    output_path = Path('/tmp/pipeline_data/raw/user_events.parquet')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    print(f"Extracted {len(df)} records to {output_path}")
    return str(output_path)

def transform_data(**context):
    """Transform and engineer features"""
    print("Transforming data...")
    
    ti = context['task_instance']
    input_path = ti.xcom_pull(task_ids='extract_task')
    
    df = pd.read_parquet(input_path)
    
    # Feature engineering
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['is_purchase'] = (df['event_type'] == 'purchase').astype(int)
    df['amount_log'] = df['amount'].apply(lambda x: np.log1p(x))
    
    # User aggregations
    user_stats = df.groupby('user_id').agg({
        'amount': ['sum', 'mean', 'count'],
        'is_purchase': 'sum'
    }).reset_index()
    user_stats.columns = ['user_id', 'total_amount', 'avg_amount', 'event_count', 'purchase_count']
    
    df = df.merge(user_stats, on='user_id', how='left')
    
    # Save processed data
    output_path = Path('/tmp/pipeline_data/processed/features.parquet')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    print(f"Transformed data with {len(df.columns)} features saved to {output_path}")
    return str(output_path)

def load_data(**context):
    """Load data to feature store"""
    print("Loading data to feature store...")
    
    ti = context['task_instance']
    input_path = ti.xcom_pull(task_ids='transform_task')
    
    df = pd.read_parquet(input_path)
    
    # Simulate loading to feature store
    feature_store_path = Path('/tmp/pipeline_data/feature_store/latest.parquet')
    feature_store_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(feature_store_path, index=False)
    
    print(f"Loaded {len(df)} records to feature store")
    
    # Generate metrics
    metrics = {
        'total_records': int(len(df)),
        'total_users': int(df['user_id'].nunique()),
        'total_purchases': int(df['is_purchase'].sum()),
        'avg_amount': float(df['amount'].mean()),
        'processed_at': datetime.now().isoformat()
    }
    
    metrics_path = Path('/tmp/pipeline_data/metrics/ingestion_metrics.json')
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics

dag = DAG(
    'data_ingestion_dag',
    default_args=default_args,
    description='Extract, transform, and load user event data',
    schedule_interval='@hourly',
    catchup=False,
    tags=['etl', 'ml-pipeline']
)

extract_task = PythonOperator(
    task_id='extract_task',
    python_callable=extract_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_task',
    python_callable=transform_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_task',
    python_callable=load_data,
    dag=dag,
)

extract_task >> transform_task >> load_task
