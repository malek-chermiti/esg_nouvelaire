#!/usr/bin/env python
"""Check if recommendations are in the database."""

from app.database import SessionLocal
from app.models.models import Recommendation, Anomaly

db = SessionLocal()

anomaly_count = db.query(Anomaly).count()
recommendation_count = db.query(Recommendation).count()

print(f"Total anomalies in DB: {anomaly_count}")
print(f"Total recommendations in DB: {recommendation_count}")
print()

# Check recent anomalies
recent_anomalies = db.query(Anomaly).order_by(Anomaly.id.desc()).limit(10).all()

for anomaly in recent_anomalies:
    rec = db.query(Recommendation).filter(Recommendation.anomaly_id == anomaly.id).first()
    status = "YES ✓" if rec else "NO ✗"
    print(f"Anomaly {anomaly.id:3d} (severity={anomaly.severity:8s}): Recommendation={status}")

print()
print("=" * 60)
if recommendation_count == 0:
    print("⚠️  WARNING: No recommendations found in database!")
    print("   This suggests AIService.generate_recommendation() is not creating records.")
else:
    print(f"✓ {recommendation_count} recommendations found")
