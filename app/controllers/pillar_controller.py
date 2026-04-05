from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.services.pillar_service import PillarService
from app.schemas.pillar_schemas import PillarScoreResponse, GlobalScoreResponse, EvolutionScoreResponse

# Default year is last year
DEFAULT_YEAR = datetime.now().year - 1


router = APIRouter(
    prefix="/pillars",
    tags=["Pillars"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/score/environnement",
    response_model=PillarScoreResponse,
    summary="Get Environnement pillar score",
    description="Calculate and retrieve Environnement pillar score with all KPIs"
)
def get_environnement_score(
    year: Optional[int] = DEFAULT_YEAR,
    db: Session = Depends(get_db)
):
    """
    Get Environnement pillar score calculation.
    
    **Parameters:**
    - **year**: Year filter (YYYY format, default: last year)
    
    **KPIs included:**
    - CO2_KG: Sum of CO2 emissions
    - WASTE_RECYCLE: Percentage of recycled waste
    - FUEL_TND: Sum of fuel surcharge amounts
    
    **Returns**: Pillar score with KPI details
    """
    try:
        return PillarService.get_pillar_score(db, 'E', year)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/score/social",
    response_model=PillarScoreResponse,
    summary="Get Social pillar score",
    description="Calculate and retrieve Social pillar score with all KPIs"
)
def get_social_score(
    year: Optional[int] = DEFAULT_YEAR,
    db: Session = Depends(get_db)
):
    """
    Get Social pillar score calculation.
    
    **Parameters:**
    - **year**: Year filter (YYYY format, default: last year)
    
    **KPIs included:**
    - EMP_RETENTION: Employee retention percentage
    - ACCIDENTS: Number of work accidents
    - TRAINING_H: Total training hours
    
    **Returns**: Pillar score with KPI details
    """
    try:
        return PillarService.get_pillar_score(db, 'S', year)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/score/gouvernance",
    response_model=PillarScoreResponse,
    summary="Get Gouvernance pillar score",
    description="Calculate and retrieve Gouvernance pillar score with all KPIs"
)
def get_gouvernance_score(
    year: Optional[int] = DEFAULT_YEAR,
    db: Session = Depends(get_db)
):
    """
    Get Gouvernance pillar score calculation.
    
    **Parameters:**
    - **year**: Year filter (YYYY format, default: last year)
    
    **KPIs included:**
    - PAYMENT_TRACE: Percentage of traceable payments
    - TAX_PAID: Percentage of paid taxes
    - AVIA_ACTIVE: Percentage of active aviation licenses
    
    **Returns**: Pillar score with KPI details
    """
    try:
        return PillarService.get_pillar_score(db, 'G', year)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/score/global",
    response_model=GlobalScoreResponse,
    summary="Get global ESG score",
    description="Calculate and retrieve global ESG score across all pillars"
)
def get_global_score(
    year: Optional[int] = DEFAULT_YEAR,
    db: Session = Depends(get_db)
):
    """
    Get global ESG score calculation.
    
    **Parameters:**
    - **year**: Year filter (YYYY format, default: last year)
    
    **Calculation:**
    - score_global = SUM(score_pillar * pillar.weight)
    - Includes scores from Environnement, Social, and Gouvernance pillars
    
    **Returns**: Global score with pillar details and weights
    """
    try:
        return PillarService.get_global_score(db, year)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/score/evolution",
    response_model=EvolutionScoreResponse,
    summary="Get monthly ESG scores evolution",
    description="Calculate and retrieve monthly ESG scores for 12 months"
)
def get_evolution_score(
    year: Optional[int] = DEFAULT_YEAR,
    db: Session = Depends(get_db)
):
    """
    Get monthly ESG scores evolution over 12 months.
    
    **Parameters:**
    - **year**: Year filter (YYYY format, default: last year)
    
    **Returns**: Monthly scores for:
    - global: Global ESG score across all pillars
    - E: Environnement pillar score
    - S: Social pillar score
    - G: Gouvernance pillar score
    
    **Format**:
    ```
    {
      "labels": ["Jan", "Fév", "Mar", ...],
      "series": {
        "global": [score1, score2, ...],
        "E": [score1, score2, ...],
        "S": [score1, score2, ...],
        "G": [score1, score2, ...]
      }
    }
    ```
    """
    try:
        return PillarService.get_monthly_scores(db, year)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
