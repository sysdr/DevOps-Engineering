import asyncio
import logging
import re
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

class QueryOptimizer:
    def __init__(self):
        self.slow_queries = []
        self.query_patterns = Counter()
        self.recommendations = []
        self.analysis_interval = 300  # 5 minutes
        self.slow_query_threshold = 100  # ms
        self.running = False
        
    async def run(self):
        """Main optimizer loop"""
        self.running = True
        logger.info("Query Optimizer started")
        
        while self.running:
            try:
                await self.analyze_queries()
                await self.generate_recommendations()
                await asyncio.sleep(self.analysis_interval)
            except Exception as e:
                logger.error(f"Optimizer error: {e}")
                await asyncio.sleep(10)
    
    async def analyze_queries(self):
        """Analyze slow queries"""
        # Simulate query log analysis
        # In production, parse actual database logs
        simulated_slow_queries = [
            {
                'query': 'SELECT * FROM users WHERE email = ?',
                'duration_ms': 250,
                'table': 'users',
                'columns': ['email'],
                'execution_plan': 'Seq Scan on users',
                'rows_examined': 150000
            },
            {
                'query': 'SELECT * FROM orders WHERE user_id = ? AND status = ?',
                'duration_ms': 180,
                'table': 'orders',
                'columns': ['user_id', 'status'],
                'execution_plan': 'Seq Scan on orders',
                'rows_examined': 50000
            },
            {
                'query': 'SELECT * FROM products WHERE category = ? ORDER BY created_at DESC',
                'duration_ms': 320,
                'table': 'products',
                'columns': ['category', 'created_at'],
                'execution_plan': 'Seq Scan on products',
                'rows_examined': 80000
            }
        ]
        
        for query in simulated_slow_queries:
            if query['duration_ms'] > self.slow_query_threshold:
                self.slow_queries.append(query)
                pattern = self.extract_pattern(query['query'])
                self.query_patterns[pattern] += 1
        
        # Keep only recent queries
        self.slow_queries = self.slow_queries[-100:]
    
    def extract_pattern(self, query):
        """Extract query pattern for grouping"""
        # Normalize query by removing parameter values
        pattern = re.sub(r"'[^']*'", '?', query)
        pattern = re.sub(r'\b\d+\b', '?', pattern)
        return pattern
    
    async def generate_recommendations(self):
        """Generate index recommendations"""
        recommendations = []
        
        # Group queries by table
        table_queries = {}
        for query in self.slow_queries:
            table = query['table']
            if table not in table_queries:
                table_queries[table] = []
            table_queries[table].append(query)
        
        # Generate index recommendations
        for table, queries in table_queries.items():
            # Find common columns in WHERE/JOIN clauses
            column_usage = Counter()
            for query in queries:
                for col in query['columns']:
                    column_usage[col] += 1
            
            # Recommend indexes for frequently queried columns
            for col, count in column_usage.most_common(3):
                impact_score = count * max(q['duration_ms'] for q in queries)
                
                recommendation = {
                    'table': table,
                    'column': col,
                    'index_name': f'idx_{table}_{col}',
                    'statement': f'CREATE INDEX idx_{table}_{col} ON {table}({col});',
                    'impact_score': impact_score,
                    'affected_queries': count,
                    'estimated_improvement': f'{min(70, impact_score / 100):.0f}%'
                }
                recommendations.append(recommendation)
        
        # Sort by impact score
        recommendations.sort(key=lambda x: x['impact_score'], reverse=True)
        self.recommendations = recommendations[:10]
        
        if self.recommendations:
            logger.info(f"Generated {len(self.recommendations)} index recommendations")
            for rec in self.recommendations[:3]:
                logger.info(f"  Top recommendation: {rec['statement']}")
    
    def get_recommendations(self):
        """Get current recommendations"""
        return {
            'recommendations': self.recommendations,
            'slow_query_count': len(self.slow_queries),
            'query_patterns': dict(self.query_patterns.most_common(5)),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def is_healthy(self):
        return self.running
