
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.models import Anomaly, Kpi
from app.schemas.schemas import AnomalyResponse, AnomalyUpdate
from app.services.co2_service import Co2Service
from app.services.fuel_surcharge_service import FuelSurchargeService
from app.services.employee_service import EmployeeService
from app.services.training_service import TrainingService
from app.services.work_accident_service import WorkAccidentService
from app.services.tax_obligation_service import TaxObligationService


router = APIRouter(
    prefix="/api/anomalies",
    tags=["Anomalies"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/detect/{kpi_code}",
    response_model=List[AnomalyResponse],
    summary="Détecter les anomalies pour un KPI",
    description="Lance la détection d'anomalies pour le KPI spécifié. Retourne la liste des nouvelles anomalies détectées."
)
def detect_anomalies(
    kpi_code: str,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Détecte les anomalies pour un KPI spécifique.

    Args:
        kpi_code: Code du KPI (co2, fuel_surcharge, PARITE_HF, FORMATION, LTIR, TAX_OBLIGAT)
        year: Année à analyser (optionnel, défaut: année en cours)
        db: Session de base de données

    Returns:
        Liste des anomalies détectées

    Raises:
        HTTPException: Si le kpi_code est inconnu
    """
    # Default to current year if not provided
    if year is None:
        year = datetime.now().year

    normalized_kpi_code = kpi_code.strip().upper()

    kpi = db.query(Kpi).filter(func.upper(Kpi.code) == normalized_kpi_code).first()
    if not kpi:
        raise HTTPException(
            status_code=404,
            detail=f"KPI code '{kpi_code}' non reconnu. Codes valides: co2, fuel_surcharge, PARITE_HF, FORMATION, LTIR, TAX_OBLIGAT"
        )

    # Call the appropriate service method based on kpi_code
    created_anomalies = []
    if normalized_kpi_code == "CO2":
        created_anomalies = Co2Service.detect_monthly_anomalies(db, year) or []
    elif normalized_kpi_code == "FUEL_SURCHARGE":
        created_anomalies = FuelSurchargeService.detect_monthly_anomalies(db, year) or []
    elif normalized_kpi_code == "PARITE_HF":
        created_anomalies = EmployeeService.detect_parity_anomalies(db) or []
    elif normalized_kpi_code == "FORMATION":
        created_anomalies = TrainingService.detect_quarterly_anomalies(db, year) or []
    elif normalized_kpi_code == "LTIR":
        created_anomalies = WorkAccidentService.detect_ltir_anomalies(db, year) or []
    elif normalized_kpi_code == "TAX_OBLIGAT":
        created_anomalies = TaxObligationService.detect_monthly_anomalies(db, year) or []

    return created_anomalies


@router.get(
    "/",
    response_model=List[AnomalyResponse],
    summary="Récupérer toutes les anomalies",
    description="Retourne la liste de toutes les anomalies, filtrées par statut."
)
def get_anomalies(
    status: Optional[str] = "NEW",
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les anomalies filtrées par statut.

    Args:
        status: Statut des anomalies à récupérer (NEW, RESOLVED, etc.)
        db: Session de base de données

    Returns:
        Liste des anomalies
    """
    query = db.query(Anomaly)

    if status:
        query = query.filter(Anomaly.status == status)

    anomalies = query.order_by(Anomaly.date_detected.desc()).all()

    return anomalies


@router.patch(
    "/{anomaly_id}/resolve",
    response_model=AnomalyResponse,
    summary="Résoudre une anomalie",
    description="Change le statut d'une anomalie à 'RESOLVED'."
)
def resolve_anomaly(
    anomaly_id: int,
    anomaly_update: AnomalyUpdate,
    db: Session = Depends(get_db)
):
    """
    Résout une anomalie en changeant son statut.

    Args:
        anomaly_id: ID de l'anomalie à résoudre
        anomaly_update: Données de mise à jour (statut)
        db: Session de base de données

    Returns:
        Anomalie mise à jour

    Raises:
        HTTPException: Si l'anomalie n'existe pas
    """
    # Get the anomaly
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomalie non trouvée")

    # Update the status
    anomaly.status = anomaly_update.status
    db.commit()
    db.refresh(anomaly)

    return anomaly
