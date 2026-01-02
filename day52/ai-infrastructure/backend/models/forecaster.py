import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import asyncpg
from datetime import datetime, timedelta
from typing import List, Tuple

class TimeSeriesForecaster:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.models = {}
        self.scalers = {}
        self.window_size = 60  # 60 data points (10 minutes at 10s intervals)
        self.forecast_horizon = 90  # 15 minutes ahead
        
    async def prepare_training_data(self, metric_name: str) -> Tuple[np.ndarray, np.ndarray]:
        """Fetch and prepare historical data for training"""
        # Get last 7 days of data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        rows = await self.db_pool.fetch('''
            SELECT time, value
            FROM metrics
            WHERE metric_name = $1
            AND time BETWEEN $2 AND $3
            ORDER BY time ASC
        ''', metric_name, start_time, end_time)
        
        if len(rows) < 1000:
            return None, None
            
        values = np.array([float(row['value']) for row in rows])
        
        # Create sliding windows
        X, y = [], []
        for i in range(len(values) - self.window_size - self.forecast_horizon):
            X.append(values[i:i+self.window_size])
            y.append(values[i+self.window_size+self.forecast_horizon])
            
        return np.array(X), np.array(y)
    
    async def train_model(self, metric_name: str):
        """Train forecasting model for specific metric"""
        print(f"Training forecaster for {metric_name}...")
        
        X, y = await self.prepare_training_data(metric_name)
        
        if X is None:
            print(f"Insufficient data for {metric_name}")
            return
            
        # Add time-based features
        X_enhanced = np.column_stack([
            X,
            np.array([row.mean() for row in X]),  # Mean
            np.array([row.std() for row in X]),   # Std dev
            np.array([row.max() - row.min() for row in X])  # Range
        ])
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_enhanced)
        
        # Train Random Forest model
        model = RandomForestRegressor(
            n_estimators=50,
            max_depth=20,
            min_samples_split=5,
            random_state=42
        )
        model.fit(X_scaled, y)
        
        # Store model and scaler
        self.models[metric_name] = model
        self.scalers[metric_name] = scaler
        
        # Calculate training accuracy
        predictions = model.predict(X_scaled)
        mae = np.mean(np.abs(predictions - y))
        rmse = np.sqrt(np.mean((predictions - y) ** 2))
        
        print(f"Model trained for {metric_name}: MAE={mae:.2f}, RMSE={rmse:.2f}")
        
        # Store performance
        await self.db_pool.execute('''
            INSERT INTO model_performance (timestamp, model_name, mae, rmse, accuracy)
            VALUES ($1, $2, $3, $4, $5)
        ''', datetime.now(), metric_name, mae, rmse, 100 - (mae / y.mean() * 100))
        
    async def predict(self, metric_name: str, recent_values: List[float]) -> Tuple[float, float, float]:
        """Make prediction with confidence intervals"""
        if metric_name not in self.models:
            return None, None, None
            
        model = self.models[metric_name]
        scaler = self.scalers[metric_name]
        
        # Prepare input
        recent_array = np.array(recent_values[-self.window_size:])
        if len(recent_array) < self.window_size:
            return None, None, None
        
        # Calculate features same way as training
        mean_val = recent_array.mean()
        std_val = recent_array.std()
        range_val = recent_array.max() - recent_array.min()
        
        # Create feature vector: flatten window + additional features
        X_input = np.concatenate([
            recent_array,
            np.array([mean_val]),
            np.array([std_val]),
            np.array([range_val])
        ]).reshape(1, -1)
        
        X_scaled = scaler.transform(X_input)
        
        # Predict
        prediction = model.predict(X_scaled)[0]
        
        # Estimate confidence intervals using tree variance
        tree_predictions = np.array([tree.predict(X_scaled)[0] for tree in model.estimators_])
        confidence_lower = np.percentile(tree_predictions, 5)
        confidence_upper = np.percentile(tree_predictions, 95)
        
        return prediction, confidence_lower, confidence_upper

class AnomalyDetector:
    def __init__(self):
        self.statistical_threshold = 3.0  # Z-score threshold
        self.window_size = 100
        
    def detect_statistical(self, recent_values: List[float], current_value: float) -> bool:
        """Statistical anomaly detection using Z-score"""
        if len(recent_values) < 30:
            return False
            
        mean = np.mean(recent_values)
        std = np.std(recent_values)
        
        if std == 0:
            return False
            
        z_score = abs((current_value - mean) / std)
        return z_score > self.statistical_threshold
    
    def detect_isolation_forest(self, recent_values: List[float], current_value: float) -> bool:
        """Simplified isolation-based detection"""
        if len(recent_values) < 50:
            return False
            
        # Check if value is isolated (far from neighbors)
        sorted_vals = sorted(recent_values + [current_value])
        current_idx = sorted_vals.index(current_value)
        
        if current_idx == 0:
            gap_left = abs(sorted_vals[1] - current_value)
            avg_gap = np.mean(np.diff(sorted_vals[1:]))
            return gap_left > 3 * avg_gap
        elif current_idx == len(sorted_vals) - 1:
            gap_right = abs(current_value - sorted_vals[-2])
            avg_gap = np.mean(np.diff(sorted_vals[:-1]))
            return gap_right > 3 * avg_gap
        else:
            gap = min(abs(current_value - sorted_vals[current_idx-1]),
                     abs(sorted_vals[current_idx+1] - current_value))
            avg_gap = np.mean(np.diff(sorted_vals))
            return gap > 3 * avg_gap
    
    def detect_rate_change(self, recent_values: List[float]) -> bool:
        """Detect sudden rate of change"""
        if len(recent_values) < 10:
            return False
            
        # Compare recent rate to historical rate
        recent_rate = abs(recent_values[-1] - recent_values[-5]) / 5
        historical_rates = [abs(recent_values[i] - recent_values[i-5]) / 5 
                           for i in range(5, len(recent_values)-5)]
        
        if not historical_rates:
            return False
            
        avg_rate = np.mean(historical_rates)
        return recent_rate > 5 * avg_rate
    
    async def detect(self, metric_name: str, current_value: float, 
                    recent_values: List[float], db_pool) -> dict:
        """Run all detectors and return results"""
        votes = {
            'statistical': self.detect_statistical(recent_values, current_value),
            'isolation': self.detect_isolation_forest(recent_values, current_value),
            'rate_change': self.detect_rate_change(recent_values + [current_value])
        }
        
        is_anomaly = sum(votes.values()) >= 2  # 2 out of 3 votes
        
        if is_anomaly:
            expected = np.mean(recent_values) if recent_values else current_value
            severity = 'high' if sum(votes.values()) == 3 else 'medium'
            
            await db_pool.execute('''
                INSERT INTO anomalies (detected_at, metric_name, value, expected_value, severity, detector_votes)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', datetime.now(), metric_name, current_value, expected, severity, 
                 str(votes))
            
            print(f"🚨 Anomaly detected: {metric_name}={current_value:.2f} (expected ~{expected:.2f})")
        
        return {'is_anomaly': is_anomaly, 'votes': votes, 'severity': severity if is_anomaly else 'none'}
