#!/usr/bin/env python
"""Test AIService directly."""

from app.database import SessionLocal
from app.models.models import Anomaly, Recommendation
from app.services.ai_service import AIService

db = SessionLocal()

# Get an existing anomaly
anomaly = db.query(Anomaly).first()

if anomaly:
    print(f"Testing AIService with anomaly {anomaly.id}")
    print(f"  - KPI ID: {anomaly.kpi_id}")
    print(f"  - Severity: {anomaly.severity}")
    print(f"  - Description: {anomaly.description[:50]}")
    
    # Check if it has a recommendation
    has_rec = db.query(Recommendation).filter(Recommendation.anomaly_id == anomaly.id).first()
    print(f"  - Existing recommendation: {'YES' if has_rec else 'NO'}")
    
    # Try to generate recommendation
    print("\nCalling AIService.generate_recommendation()...")
    try:
        rec = AIService.generate_recommendation(db, anomaly)
        if rec:
            print(f"✓ SUCCESS! Recommendation created:")
            print(f"  - ID: {rec.id}")
            print(f"  - Title: {rec.title}")
            print(f"  - Priority: {rec.priority}")
        else:
            print("✗ FAILED: AIService returned None")
    except Exception as e:
        print(f"✗ EXCEPTION: {type(e).__name__}: {str(e)}")
else:
    print("No anomalies found in database")
