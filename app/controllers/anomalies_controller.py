from fastapi import APIRouter, HTTPException
from app.services.anomaly_detection_service import AnomalyDetectionService
from app.schemas.anomaly_schemas import AnomalyListResponse, AnomalyCriticalResponse, AnomalyResponse
from app.database import SessionLocal
from typing import List

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies"])


@router.get("/", response_model=AnomalyListResponse)
def get_anomalies():
    """Get all open anomalies"""
    db = SessionLocal()
    try:
        anomalies = AnomalyDetectionService.get_open_anomalies(db)
        return {"total": len(anomalies), "anomalies": [AnomalyResponse.model_validate(a, from_attributes=True) for a in anomalies]}
    finally:
        db.close()


@router.get("/critical", response_model=AnomalyCriticalResponse)
def get_critical_anomalies():
    """Get critical anomalies"""
    db = SessionLocal()
    try:
        anomalies = AnomalyDetectionService.get_critical_anomalies(db)
        return {"total_critical": len(anomalies), "anomalies": [AnomalyResponse.model_validate(a, from_attributes=True) for a in anomalies]}
    finally:
        db.close()


@router.post("/detect")
def detect_anomalies():
    """Detect anomalies from KPI data"""
    anomalies = AnomalyDetectionService.detect_anomalies()
    return {"detected": len(anomalies), "anomalies": [AnomalyResponse.model_validate(a, from_attributes=True) for a in anomalies]}


@router.post("/detect/monthly")
def detect_monthly_anomalies():
    """Detect monthly anomalies for all KPIs"""
    monthly_anomalies = AnomalyDetectionService.detect_all_monthly_anomalies()
    return {
        "total_monthly_anomalies": len(monthly_anomalies),
        "anomalies": monthly_anomalies
    }


@router.post("/detect/monthly/{kpi_code}")
def detect_kpi_monthly_anomalies(kpi_code: str):
    """Detect monthly anomalies for a specific KPI code"""
    monthly_anomalies = AnomalyDetectionService.detect_monthly_anomalies(kpi_code)
    return {
        "kpi_code": kpi_code,
        "total_anomalies": len(monthly_anomalies),
        "anomalies": monthly_anomalies
    }


@router.patch("/{anomaly_id}/resolve")
def resolve_anomaly(anomaly_id: int):
    """Mark anomaly as resolved"""
    db = SessionLocal()
    try:
        anomaly = AnomalyDetectionService.mark_resolved(db, anomaly_id)
        if not anomaly:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        return {"message": "Resolved", "anomaly": AnomalyResponse.model_validate(anomaly, from_attributes=True)}
    finally:
        db.close()


@router.get("/stats")
def get_stats():
    """Get anomaly statistics"""
    db = SessionLocal()
    try:
        return AnomalyDetectionService.get_stats(db)
    finally:
        db.close()
