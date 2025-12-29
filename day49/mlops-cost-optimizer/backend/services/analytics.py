import asyncpg
from typing import List, Dict
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CostAnalytics:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def get_cost_summary(self, days: int = 7) -> Dict:
        """Get cost summary for last N days"""
        start_date = datetime.now() - timedelta(days=days)
        
        async with self.db_pool.acquire() as conn:
            # Total cost
            total = await conn.fetchval('''
                SELECT COALESCE(SUM(cost), 0) FROM cost_records
                WHERE timestamp >= $1
            ''', start_date)
            
            # By team
            team_costs = await conn.fetch('''
                SELECT team, SUM(cost) as total_cost
                FROM cost_records
                WHERE timestamp >= $1
                GROUP BY team
                ORDER BY total_cost DESC
            ''', start_date)
            
            # By project
            project_costs = await conn.fetch('''
                SELECT project, SUM(cost) as total_cost
                FROM cost_records
                WHERE timestamp >= $1
                GROUP BY project
                ORDER BY total_cost DESC
            ''', start_date)
            
            # Daily trend
            daily_trend = await conn.fetch('''
                SELECT DATE(timestamp) as date, SUM(cost) as daily_cost
                FROM cost_records
                WHERE timestamp >= $1
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''', start_date)
        
        return {
            "total_cost": float(total),
            "by_team": {row["team"]: float(row["total_cost"]) for row in team_costs},
            "by_project": {row["project"]: float(row["total_cost"]) for row in project_costs},
            "daily_trend": [
                {"date": row["date"].isoformat(), "cost": float(row["daily_cost"])}
                for row in daily_trend
            ]
        }
    
    async def get_team_forecast(self, team: str) -> Dict:
        """Forecast end-of-month spending for team"""
        today = datetime.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        days_elapsed = (today - month_start).days + 1
        days_in_month = 30  # Simplified
        
        async with self.db_pool.acquire() as conn:
            current_spend = await conn.fetchval('''
                SELECT COALESCE(SUM(cost), 0) FROM cost_records
                WHERE team = $1 AND timestamp >= $2
            ''', team, month_start)
        
        daily_average = current_spend / days_elapsed if days_elapsed > 0 else 0
        forecast = daily_average * days_in_month
        
        return {
            "team": team,
            "current_spend": float(current_spend),
            "daily_average": float(daily_average),
            "forecast_spend": float(forecast),
            "days_elapsed": days_elapsed,
            "days_remaining": days_in_month - days_elapsed
        }
    
    async def calculate_roi(self, model_id: str, revenue_impact: float) -> Dict:
        """Calculate ROI for a model"""
        # Get model costs
        async with self.db_pool.acquire() as conn:
            model_cost = await conn.fetchval('''
                SELECT COALESCE(SUM(cost), 0) FROM cost_records
                WHERE project = $1
            ''', model_id)
        
        model_cost = float(model_cost) if model_cost else 1.0
        roi = ((revenue_impact - model_cost) / model_cost) * 100
        
        return {
            "model_id": model_id,
            "total_cost": model_cost,
            "revenue_impact": revenue_impact,
            "roi_percent": roi,
            "net_value": revenue_impact - model_cost
        }
