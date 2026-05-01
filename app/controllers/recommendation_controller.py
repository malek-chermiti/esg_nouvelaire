import json

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

    structured_description = {}
    if recommendation.description:
        try:
            structured_description = json.loads(recommendation.description)
        except json.JSONDecodeError:
            structured_description = {}

    analysis = structured_description.get("analysis") or recommendation.description
    recommendation_text = structured_description.get("recommendation") or (
        "Mettre en place un plan d'action correctif, suivre l'indicateur sur les prochains cycles "
        "et documenter la cause racine pour éviter la recurrence."
    )

    return {
        "status": "Success",
        "data": {
            "title": recommendation.title,
            "priority": recommendation.priority,
            "analysis": analysis,
            "recommendation": recommendation_text,
            "impact_estimated": structured_description.get("impact_estimated", recommendation.impact_estimated),
            "description": recommendation.description,
        },
    }
