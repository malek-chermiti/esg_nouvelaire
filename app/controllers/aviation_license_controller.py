from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.aviation_license_service import AviationLicenseService
from app.schemas.aviation_license_schemas import AviationLicenseResponse


router = APIRouter(
    prefix="/api/aviation-licenses",
    tags=["Aviation Licenses"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/by-period-and-type",
    response_model=AviationLicenseResponse,
    summary="Get aviation licenses by period and type",
    description="Get active and pending aviation licenses grouped by period (YYYY-MM) and license type for a specific year"
)
def get_aviation_licenses_by_period_and_type(
    year: Optional[int] = Query(None, description="Year (YYYY format). Defaults to previous year"),
    db: Session = Depends(get_db)
):
    """
    Get active and pending aviation licenses grouped by period and license type for a specific year.
    
    Query logic:
    - Filter: status IN ('ACTIVE', 'PENDING') and year = specified year (or previous year by default)
    - Group by: period (YYYY-MM, based on period_date) and license_type
    - Sum: cost_tnd for each group
    - Order by: period ascending, then license_type
    
    - **year**: Optional year filter (YYYY format, defaults to previous year)
    
    Example response:
    ```
    {
        "year": 2025,
        "periods": [
            {
                "period": "2025-01",
                "licenses_by_type": [
                    {
                        "license_type": "Pilot License",
                        "total_cost": 5000.500
                    },
                    {
                        "license_type": "Aircraft Maintenance",
                        "total_cost": 3200.750
                    }
                ],
                "total_period": 8201.250
            },
            {
                "period": "2025-02",
                "licenses_by_type": [
                    {
                        "license_type": "Route Authorization",
                        "total_cost": 2450.000
                    }
                ],
                "total_period": 2450.000
            }
        ]
    }
    ```
    """
    try:
        return AviationLicenseService.get_active_pending_licenses_by_period_and_type(db, year)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
