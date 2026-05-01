#!/usr/bin/env python
"""Check which anomalies have recommendations."""

from app.database import SessionLocal
from app.models.models import Recommendation, Anomaly

db = SessionLocal()

anomaly_count = db.query(Anomaly).count()
recommendation_count = db.query(Recommendation).count()

print(f"Total anomalies: {anomaly_count}")
print(f"Total recommendations: {recommendation_count}")
print()

# Check recent anomalies in 2025
anomalies_2025 = db.query(Anomaly).filter(
    Anomaly.description.like("%2025%")
).order_by(Anomaly.id.desc()).limit(10).all()

print(f"Recent anomalies (year 2025):")
for anomaly in anomalies_2025:
    rec = db.query(Recommendation).filter(Recommendation.anomaly_id == anomaly.id).first()
    status = "[YES]" if rec else "[NO ]"
    print(f"  ID {anomaly.id:3d} ({anomaly.severity:8s}): {status} recommendation")

print()

# Check all anomalies with recommendations
print("Anomalies WITH recommendations:")
all_with_recs = db.query(Anomaly).join(
    Recommendation, Anomaly.id == Recommendation.anomaly_id
).order_by(Anomaly.id.desc()).limit(15).all()

for anomaly in all_with_recs:
    rec = db.query(Recommendation).filter(Recommendation.anomaly_id == anomaly.id).first()
    print(f"  ID {anomaly.id:3d}: {rec.title[:50]}")
