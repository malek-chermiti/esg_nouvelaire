from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.waste_management_service import WasteManagementService
from app.schemas.waste_management_schemas import WasteRecyclingRateKpiDetailResponse


router = APIRouter(
    prefix="/api/kpi/waste-management",
    tags=["Waste Management KPI"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/recycling-rate",
    response_model=WasteRecyclingRateKpiDetailResponse,
    summary="Get monthly Waste Management recycling rate",
    description="Calculate and retrieve monthly recycling rate KPI scores (rate = (recycled_weight / total_weight) * 100)"
)
def get_monthly_recycling_rate(
    year: Optional[int] = None,
    kpi_code: str = "WASTE",
    db: Session = Depends(get_db)
):
    """
    Get monthly recycling rate KPI scores by month.
    
    - **year**: Optional year filter (YYYY format)
    - **kpi_code**: KPI code (default: recycling_rate)
    - **Returns**: Monthly recycling rates with total and recycled weights
    
    Example response:
    ```
    {
        "kpi_code": "recycling_rate",
        "kpi_name": "Recycling Rate",
        "unit": "%",
        "monthly_scores": [
            {
                "month": "2026-04",
                "total_weight_kg": 1000.0,
                "recycled_weight_kg": 750.0,
                "recycling_rate": 75.0
            }
        ]
    }
    ```
    """
    try:
        return WasteManagementService.get_monthly_recycling_rate(
            db=db,
            kpi_code=kpi_code,
            year=year
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
