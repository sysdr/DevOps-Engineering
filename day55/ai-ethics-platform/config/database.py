from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/ai_ethics")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ModelMetadata(Base):
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, unique=True, index=True)
    name = Column(String)
    version = Column(String)
    owner = Column(String)
    description = Column(Text)
    risk_level = Column(String)  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON)

class BiasAnalysis(Base):
    __tablename__ = "bias_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, index=True)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    demographic_parity = Column(Float)
    equalized_odds_tpr = Column(Float)
    equalized_odds_fpr = Column(Float)
    statistical_significance = Column(Float)
    passed = Column(Boolean)
    report = Column(JSON)

class FairnessMetric(Base):
    __tablename__ = "fairness_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name = Column(String)
    metric_value = Column(Float)
    group = Column(String)
    metadata_json = Column(JSON)

class GovernanceWorkflow(Base):
    __tablename__ = "governance_workflow"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, index=True)
    current_state = Column(String, index=True)
    submitted_by = Column(String)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    history = Column(JSON)
    approvals = Column(JSON)

class Explanation(Base):
    __tablename__ = "explanations"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String, unique=True, index=True)
    model_id = Column(String, index=True)
    input_data = Column(JSON)
    prediction = Column(Float)
    shap_values = Column(JSON)
    natural_language = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
