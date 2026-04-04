from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.tax_obligation_service import TaxObligationService
from app.schemas.tax_obligation_schemas import TaxObligationResponse


router = APIRouter(
    prefix="/api/tax-obligations",
    tags=["Tax Obligations"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/by-period-and-type",
    response_model=TaxObligationResponse,
    summary="Get tax obligations by period and type",
    description="Get all tax obligations grouped by period (YYYY-MM) and tax type for a specific year"
)
def get_tax_obligations_by_period_and_type(
    year: Optional[int] = Query(None, description="Year (YYYY format). Defaults to previous year"),
    db: Session = Depends(get_db)
):
    """
    Get tax obligations grouped by period and tax type for a specific year.
    
    Query logic:
    - Filter: year = specified year (or previous year by default)
    - Group by: period (YYYY-MM, based on period_start) and tax_type
    - Sum: amount_tnd for each group
    - Order by: period ascending, then tax_type
    
    - **year**: Optional year filter (YYYY format, defaults to previous year)
    
    Example response:
    ```
    {
        "year": 2025,
        "periods": [
            {
                "period": "2025-01",
                "taxes_by_type": [
                    {
                        "tax_type": "VAT",
                        "total_amount": 15000.500
                    },
                    {
                        "tax_type": "Corporate Tax",
                        "total_amount": 8200.750
                    }
                ],
                "total_period": 23201.250
            },
            {
                "period": "2025-02",
                "taxes_by_type": [
                    {
                        "tax_type": "VAT",
                        "total_amount": 16450.000
                    }
                ],
                "total_period": 16450.000
            }
        ]
    }
    ```
    """
    try:
        return TaxObligationService.get_tax_obligations_by_period_and_type(db, year)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
