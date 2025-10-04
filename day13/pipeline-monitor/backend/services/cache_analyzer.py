import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CacheAnalysis:
    hit_rate: float
    size_mb: float
    effectiveness_score: float
    recommendations: List[str]

class CacheAnalyzer:
    def __init__(self):
        self.cache_data = {}
        
    def analyze_cache_performance(self, build_id: str, cache_stats: Dict) -> CacheAnalysis:
        hits = cache_stats.get('hits', 0)
        misses = cache_stats.get('misses', 0)
        total = hits + misses
        
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        # Simulated cache size analysis
        size_mb = cache_stats.get('size_mb', 0)
        
        # Calculate effectiveness score (0-100)
        effectiveness_score = min(100, hit_rate * 0.7 + (100 - min(size_mb / 1000 * 100, 100)) * 0.3)
        
        recommendations = self._generate_recommendations(hit_rate, size_mb)
        
        return CacheAnalysis(
            hit_rate=hit_rate,
            size_mb=size_mb,
            effectiveness_score=effectiveness_score,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, hit_rate: float, size_mb: float) -> List[str]:
        recommendations = []
        
        if hit_rate < 50:
            recommendations.append("Consider expanding cache scope to include more dependencies")
            recommendations.append("Analyze frequently rebuilt components for caching opportunities")
        
        if hit_rate > 90:
            recommendations.append("Excellent cache performance! Monitor for cache invalidation patterns")
        
        if size_mb > 5000:  # 5GB
            recommendations.append("Large cache size detected - consider implementing cache cleanup policies")
        
        if size_mb < 100:  # 100MB
            recommendations.append("Small cache size - consider increasing cache allocation for better performance")
        
        return recommendations
