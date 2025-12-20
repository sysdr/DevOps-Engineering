#!/usr/bin/env python3
"""Data validation with Great Expectations patterns"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path

class DataValidator:
    def __init__(self):
        self.expectations = self._define_expectations()
        
    def _define_expectations(self):
        """Define validation expectations"""
        return {
            'user_id_not_null': lambda df: df['user_id'].notna().all(),
            'user_id_unique': lambda df: df['user_id'].is_unique,
            'age_in_range': lambda df: ((df['age'] >= 13) & (df['age'] <= 120)).all(),
            'event_type_valid': lambda df: df['event_type'].isin(['click', 'view', 'purchase', 'add_to_cart']).all(),
            'amount_positive': lambda df: (df['amount'] >= 0).all(),
            'timestamp_not_future': lambda df: (pd.to_datetime(df['timestamp']) <= datetime.now()).all(),
            'min_row_count': lambda df: len(df) >= 50,
            'max_null_percentage': lambda df: (df.isnull().sum().sum() / (len(df) * len(df.columns))) < 0.05,
            'amount_reasonable': lambda df: ((df['amount'] >= 0) & (df['amount'] <= 10000)).all(),
            'no_duplicate_events': lambda df: not df.duplicated().any()
        }
    
    def validate(self, df):
        """Run all validations on dataframe"""
        results = {}
        
        for name, expectation in self.expectations.items():
            try:
                passed = expectation(df)
                results[name] = {
                    'passed': bool(passed),
                    'expectation': name
                }
            except Exception as e:
                results[name] = {
                    'passed': False,
                    'expectation': name,
                    'error': str(e)
                }
        
        # Calculate validation score
        passed_count = sum(1 for r in results.values() if r['passed'])
        total_count = len(results)
        score = (passed_count / total_count) * 100
        
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'validation_score': score,
            'passed_expectations': passed_count,
            'total_expectations': total_count,
            'results': results,
            'dataset_info': {
                'row_count': len(df),
                'column_count': len(df.columns),
                'null_count': int(df.isnull().sum().sum())
            }
        }
        
        return validation_result
    
    def generate_report(self, validation_result, output_path):
        """Generate validation report"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        
        print(f"Validation report saved to {output_path}")
        return output_path

if __name__ == '__main__':
    # Example usage
    validator = DataValidator()
    
    # Load sample data
    data_path = Path('/tmp/pipeline_data/feature_store/latest.parquet')
    if data_path.exists():
        df = pd.read_parquet(data_path)
        result = validator.validate(df)
        validator.generate_report(result, '/tmp/pipeline_data/validation/ge_results.json')
        
        print(f"\nValidation Score: {result['validation_score']:.1f}%")
        print(f"Passed: {result['passed_expectations']}/{result['total_expectations']} expectations")
        
        failures = [k for k, v in result['results'].items() if not v['passed']]
        if failures:
            print(f"Failed expectations: {', '.join(failures)}")
