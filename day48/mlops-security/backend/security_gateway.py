import numpy as np
from typing import Dict, Any
import random

class SecurityGateway:
    def __init__(self):
        # Baseline statistics for models
        self.baselines = {
            "fraud_detection_v1": {
                "mean": [0.5, 0.4, 0.6],
                "std": [0.2, 0.15, 0.25],
                "range": [(0, 1), (0, 1), (0, 1)]
            }
        }
        self.adversarial_threshold = 0.3
        self.stability_threshold = 0.4
    
    def detect_adversarial(self, model_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect adversarial inputs using statistical analysis"""
        
        if model_id not in self.baselines:
            # Initialize baseline for new model
            self.baselines[model_id] = {
                "mean": [0.5] * 3,
                "std": [0.2] * 3,
                "range": [(0, 1)] * 3
            }
        
        baseline = self.baselines[model_id]
        features = input_data.get("features", [0.5, 0.5, 0.5])
        
        # Statistical outlier detection
        distance = self._calculate_statistical_distance(features, baseline)
        
        if distance > self.adversarial_threshold:
            return {
                "adversarial": True,
                "confidence": round(distance, 2),
                "reason": "statistical_outlier"
            }
        
        # Robustness testing with perturbations
        stability = self._test_input_stability(features)
        
        if stability > self.stability_threshold:
            return {
                "adversarial": True,
                "confidence": round(stability, 2),
                "reason": "unstable_predictions"
            }
        
        return {
            "adversarial": False,
            "confidence": round(max(distance, stability), 2)
        }
    
    def _calculate_statistical_distance(self, features: list, baseline: dict) -> float:
        """Calculate KL divergence approximation"""
        distance = 0.0
        for i, val in enumerate(features):
            if i < len(baseline["mean"]):
                mean = baseline["mean"][i]
                std = baseline["std"][i]
                
                # Normalized distance
                z_score = abs(val - mean) / (std + 1e-6)
                distance += z_score
        
        return distance / len(features) if features else 0.0
    
    def _test_input_stability(self, features: list) -> float:
        """Test prediction stability under perturbations"""
        num_perturbations = 5
        epsilon = 0.01
        
        predictions = []
        for _ in range(num_perturbations):
            perturbed = [f + random.gauss(0, epsilon) for f in features]
            # Simulate prediction (in real system, call actual model)
            pred = sum(perturbed) / len(perturbed)
            predictions.append(pred)
        
        # Calculate variance
        mean_pred = sum(predictions) / len(predictions)
        variance = sum((p - mean_pred) ** 2 for p in predictions) / len(predictions)
        
        return variance
