from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Recommendation


router = APIRouter(
    tags=["Recommendations"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/anomalies/{anomaly_id}/recommendation",
    summary="Afficher l'analyse et la recommandation",
)
def get_ai_recommendation(anomaly_id: int, db: Session = Depends(get_db)):
    recommendation = db.query(Recommendation).filter(
        Recommendation.anomaly_id == anomaly_id
    ).first()

    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail="Aucune analyse disponible pour cette anomalie.",
        )

    return {
        "status": "Success",
        "data": {
            "title": recommendation.title,
            "priority": recommendation.priority,
            "description": recommendation.description,
        },
    }
