from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List
import numpy as np
import sys
from pathlib import Path

# Ensure shared config is on path
ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT_DIR / "config"))
from database import get_db, Explanation, init_db
from datetime import datetime
import json

app = FastAPI(title="Explainability Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExplainRequest(BaseModel):
    model_id: str
    prediction_id: str
    input_data: Dict
    prediction: float

# Simulated SHAP value computation
def compute_shap_values(input_data: Dict, prediction: float) -> Dict:
    # Simulate feature contributions (in real system, use shap library)
    feature_importance = {}
    base_value = 0.5
    
    # Common features for a credit/loan model
    if 'credit_score' in input_data:
        score = input_data['credit_score']
        threshold = 680
        contribution = (score - threshold) * 0.002
        feature_importance['credit_score'] = contribution
    
    if 'income' in input_data:
        income = input_data['income']
        contribution = (income - 50000) * 0.000001
        feature_importance['income'] = contribution
    
    if 'debt_ratio' in input_data:
        ratio = input_data['debt_ratio']
        contribution = -(ratio - 0.35) * 0.5
        feature_importance['debt_ratio'] = contribution
    
    if 'age' in input_data:
        age = input_data['age']
        contribution = (age - 40) * 0.001
        feature_importance['age'] = contribution
    
    # Normalize to match prediction
    total_contribution = sum(feature_importance.values())
    scale = (prediction - base_value) / total_contribution if total_contribution != 0 else 1
    
    scaled_importance = {k: v * scale for k, v in feature_importance.items()}
    
    return {
        'base_value': base_value,
        'feature_contributions': scaled_importance,
        'prediction': prediction
    }

def generate_natural_language(input_data: Dict, shap_values: Dict) -> str:
    contributions = shap_values['feature_contributions']
    prediction = shap_values.get('prediction', 0.5)
    
    # Sort by absolute contribution
    sorted_features = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
    
    explanation_parts = []
    
    # Add overall prediction context
    approval_status = "likely to be approved" if prediction >= 0.5 else "likely to be rejected"
    explanation_parts.append(
        f"Based on your application details, your loan is {approval_status} "
        f"with a {prediction*100:.1f}% approval probability."
    )
    
    # Explain top 3 features
    for feature, contribution in sorted_features[:3]:  # Top 3 features
        value = input_data.get(feature, 'N/A')
        is_positive = contribution > 0
        impact_word = "increases" if is_positive else "decreases"
        
        if feature == 'credit_score':
            threshold = 680
            if value >= threshold:
                explanation_parts.append(
                    f"Your credit score of {value} is above the typical threshold of {threshold}, "
                    f"which {impact_word} your approval probability by {abs(contribution):.3f} points."
                )
            else:
                explanation_parts.append(
                    f"Your credit score of {value} is below the typical threshold of {680}, "
                    f"which {impact_word} your approval probability by {abs(contribution):.3f} points."
                )
        elif feature == 'income':
            avg_income = 50000
            if value >= avg_income:
                explanation_parts.append(
                    f"Your annual income of ${value:,} is above the average of ${avg_income:,}, "
                    f"which {impact_word} your approval probability by {abs(contribution):.3f} points."
                )
            else:
                explanation_parts.append(
                    f"Your annual income of ${value:,} is below the average of ${avg_income:,}, "
                    f"which {impact_word} your approval probability by {abs(contribution):.3f} points."
                )
        elif feature == 'debt_ratio':
            ideal_ratio = 0.35
            if value <= ideal_ratio:
                explanation_parts.append(
                    f"Your debt-to-income ratio of {value:.1%} is below the ideal ratio of {ideal_ratio:.0%}, "
                    f"which {impact_word} your approval probability by {abs(contribution):.3f} points."
                )
            else:
                explanation_parts.append(
                    f"Your debt-to-income ratio of {value:.1%} is above the ideal ratio of {ideal_ratio:.0%}, "
                    f"which {impact_word} your approval probability by {abs(contribution):.3f} points."
                )
        elif feature == 'age':
            ideal_age = 45
            age_diff = abs(value - ideal_age)
            if age_diff <= 10:
                explanation_parts.append(
                    f"Your age of {value} is within the ideal range, "
                    f"which {impact_word} your approval probability by {abs(contribution):.3f} points."
                )
            else:
                explanation_parts.append(
                    f"Your age of {value} is outside the ideal range, "
                    f"which {impact_word} your approval probability by {abs(contribution):.3f} points."
                )
    
    return " ".join(explanation_parts)

@app.post("/api/v1/explain/generate")
async def generate_explanation(request: ExplainRequest, db: Session = Depends(get_db)):
    # Compute SHAP values
    shap_values = compute_shap_values(request.input_data, request.prediction)
    
    # Generate natural language explanation
    natural_language = generate_natural_language(request.input_data, shap_values)
    
    # Store explanation
    explanation = Explanation(
        prediction_id=request.prediction_id,
        model_id=request.model_id,
        input_data=json.dumps(request.input_data),
        prediction=request.prediction,
        shap_values=json.dumps(shap_values),
        natural_language=natural_language
    )
    db.add(explanation)
    db.commit()
    
    return {
        'prediction_id': request.prediction_id,
        'shap_values': shap_values,
        'natural_language': natural_language,
        'feature_ranking': sorted(
            shap_values['feature_contributions'].items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
    }

@app.get("/api/v1/explain/{prediction_id}")
async def get_explanation(prediction_id: str, db: Session = Depends(get_db)):
    explanation = db.query(Explanation).filter(
        Explanation.prediction_id == prediction_id
    ).first()
    
    if not explanation:
        return {"error": "Explanation not found"}
    
    return {
        'prediction_id': prediction_id,
        'model_id': explanation.model_id,
        'input_data': json.loads(explanation.input_data),
        'prediction': explanation.prediction,
        'shap_values': json.loads(explanation.shap_values),
        'natural_language': explanation.natural_language,
        'created_at': explanation.created_at.isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "explainability"}

@app.on_event("startup")
async def startup():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
