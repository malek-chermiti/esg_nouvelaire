from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.work_accident_service import WorkAccidentService
from app.schemas.work_accident_schemas import (
    LTIRDetailResponse
)


router = APIRouter(
    prefix="/api/work-accidents",
    tags=["Work Accidents"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/ltir-monthly",
    response_model=LTIRDetailResponse,
    summary="Get monthly LTIR",
    description="Calculate and retrieve monthly Lost Time Injury Rate (LTIR) for a specific year"
)
def get_ltir_by_month(
    year: Optional[int] = Query(None, description="Year (YYYY format). Defaults to current year"),
    db: Session = Depends(get_db)
):
    """
    Get monthly LTIR calculations by month.
    
    Calculation process:
    1. Count lost-time accidents (is_lost_time = 1) per month
    2. Count active employees (is_active = 1)
    3. Calculate hours: heures = nb_employees × 166
    4. Calculate LTIR: LTIR = (nb_accidents × 1,000,000) / heures
    
    - **year**: Optional year filter (YYYY format, defaults to current year)
    - **Returns**: Monthly LTIR data with accidents count, active employees, hours, and LTIR values
    
    Example response:
    ```
    {
        "year": 2026,
        "monthly_data": [
            {
                "month": "2026-01",
                "nb_accidents": 2,
                "nb_active_employees": 150,
                "hours_worked": 24900,
                "ltir": 80.32
            },
            ...
        ],
        "average_ltir": 45.67
    }
    ```
    """
    try:
        return WorkAccidentService.get_ltir_by_month(db, year)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
