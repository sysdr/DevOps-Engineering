from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import numpy as np
import json
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Explainability Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExplanationRequest(BaseModel):
    prediction_id: str
    model_id: str = "default"

class ExplainabilityService:
    def __init__(self):
        self.db_pool = None
        self.model = None
        
    async def init_db(self):
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5433,
            user='postgres',
            password='postgres',
            database='monitoring'
        )
        
        # Create explanations table
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS explanations (
                    id SERIAL PRIMARY KEY,
                    prediction_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    explanation_type TEXT NOT NULL,
                    feature_importance JSONB NOT NULL,
                    base_value FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
    
    def calculate_shap_values(self, features: Dict) -> Dict:
        # Simplified SHAP calculation (in production, use actual SHAP library)
        feature_values = {k: float(v) if isinstance(v, (int, float)) else 0.0 
                         for k, v in features.items()}
        
        # Simulate SHAP value calculation
        base_value = 0.5
        shap_values = {}
        
        for feature_name, feature_value in feature_values.items():
            # Simple contribution calculation
            contribution = (feature_value / 100.0) * np.random.uniform(-0.2, 0.2)
            shap_values[feature_name] = contribution
        
        return {
            "shap_values": shap_values,
            "base_value": base_value,
            "predicted_value": base_value + sum(shap_values.values())
        }
    
    def calculate_lime_explanation(self, features: Dict) -> Dict:
        # Simplified LIME explanation
        feature_values = {k: float(v) if isinstance(v, (int, float)) else 0.0 
                         for k, v in features.items()}
        
        # Simulate local linear approximation
        weights = {}
        for feature_name, feature_value in feature_values.items():
            weight = np.random.uniform(-0.5, 0.5)
            weights[feature_name] = weight
        
        intercept = 0.5
        prediction = intercept + sum(w * feature_values[f] / 100.0 
                                    for f, w in weights.items())
        
        return {
            "weights": weights,
            "intercept": intercept,
            "local_prediction": prediction,
            "r2_score": 0.85
        }
    
    async def get_prediction_features(self, prediction_id: str):
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT features, prediction
                FROM predictions
                WHERE prediction_id = $1
                LIMIT 1
            ''', prediction_id)
            
            if not row:
                raise ValueError(f"Prediction {prediction_id} not found")
            
            return json.loads(row['features']), row['prediction']
    
    async def generate_explanation(self, prediction_id: str, model_id: str, 
                                   explanation_type: str = "shap"):
        features, prediction = await self.get_prediction_features(prediction_id)
        
        if explanation_type == "shap":
            explanation = self.calculate_shap_values(features)
        elif explanation_type == "lime":
            explanation = self.calculate_lime_explanation(features)
        else:
            raise ValueError(f"Unknown explanation type: {explanation_type}")
        
        # Store explanation
        await self.store_explanation(prediction_id, model_id, explanation_type, explanation)
        
        return explanation
    
    async def store_explanation(self, prediction_id: str, model_id: str, 
                               explanation_type: str, explanation: Dict):
        async with self.db_pool.acquire() as conn:
            feature_importance = explanation.get('shap_values') or explanation.get('weights')
            base_value = explanation.get('base_value') or explanation.get('intercept')
            
            await conn.execute('''
                INSERT INTO explanations 
                (prediction_id, model_id, explanation_type, feature_importance, base_value)
                VALUES ($1, $2, $3, $4, $5)
            ''', prediction_id, model_id, explanation_type, 
                json.dumps(feature_importance), base_value)

service = ExplainabilityService()

@app.on_event("startup")
async def startup():
    await service.init_db()
    logger.info("Explainability service started")

@app.post("/explain/shap")
async def generate_shap_explanation(request: ExplanationRequest):
    try:
        explanation = await service.generate_explanation(
            request.prediction_id, request.model_id, "shap"
        )
        return {
            "prediction_id": request.prediction_id,
            "explanation_type": "shap",
            "explanation": explanation
        }
    except Exception as e:
        logger.error(f"Error generating SHAP explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain/lime")
async def generate_lime_explanation(request: ExplanationRequest):
    try:
        explanation = await service.generate_explanation(
            request.prediction_id, request.model_id, "lime"
        )
        return {
            "prediction_id": request.prediction_id,
            "explanation_type": "lime",
            "explanation": explanation
        }
    except Exception as e:
        logger.error(f"Error generating LIME explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/explain/history/{prediction_id}")
async def get_explanation_history(prediction_id: str):
    async with service.db_pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT * FROM explanations
            WHERE prediction_id = $1
            ORDER BY created_at DESC
        ''', prediction_id)
        
        return [dict(row) for row in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
