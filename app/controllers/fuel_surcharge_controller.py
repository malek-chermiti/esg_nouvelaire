from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.fuel_surcharge_service import FuelSurchargeService
from app.schemas.fuel_surcharge_schemas import FuelSurchargeKpiDetailResponse


router = APIRouter(
    prefix="/api/kpi/fuel-surcharge",
    tags=["Fuel Surcharge KPI"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/monthly-score",
    response_model=FuelSurchargeKpiDetailResponse,
    summary="Get monthly Fuel Surcharge KPI score",
    description="Calculate and retrieve monthly Fuel Surcharge KPI scores (score = (sum(amount_tnd) / target) * 100)"
)
def get_monthly_fuel_surcharge_score(
    year: Optional[int] = None,
    kpi_code: str = "fuel_surcharge",
    db: Session = Depends(get_db)
):
    """
    Get monthly Fuel Surcharge KPI scores by month.
    
    - **year**: Optional year filter (YYYY format)
    - **kpi_code**: KPI code (default: fuel_surcharge)
    - **Returns**: Monthly scores with fuel surcharge totals and calculated percentages
    
    Example response:
    ```
    {
        "kpi_code": "fuel_surcharge",
        "kpi_name": "Fuel Surcharge",
        "unit": "TND",
        "monthly_scores": [
            {
                "month": "2026-04",
                "total_amount_tnd": 5000.0,
                "kpi_target": 10000.0,
                "score": 50.0
            }
        ]
    }
    ```
    """
    try:
        return FuelSurchargeService.get_monthly_fuel_surcharge_score(
            db=db,
            kpi_code=kpi_code,
            year=year
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
