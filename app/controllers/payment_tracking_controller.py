from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.payment_tracking_service import PaymentTrackingService
from app.schemas.payment_tracking_schemas import PaymentTrackingResponse


router = APIRouter(
    prefix="/api/payment-tracking",
    tags=["Payment Tracking"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/traceable",
    response_model=PaymentTrackingResponse,
    summary="Get traceable payments by period and mode",
    description="Get all traceable payments grouped by period (YYYY-MM) and payment mode for a specific year"
)
def get_traceable_payments(
    year: Optional[int] = Query(None, description="Year (YYYY format). Defaults to previous year"),
    db: Session = Depends(get_db)
):
    """
    Get traceable payments grouped by period and payment mode for a specific year.
    
    Only includes payments with is_traceable = 1
    
    Query logic:
    - Filter: is_traceable = 1 and year = specified year (or previous year by default)
    - Group by: period (YYYY-MM) and payment_mode
    - Sum: amount_tnd for each group
    - Order by: period ascending
    
    - **year**: Optional year filter (YYYY format, defaults to previous year)
    
    Example response:
    ```
    {
        "periods": [
            {
                "period": "2025-01",
                "payments_by_mode": [
                    {
                        "payment_mode": "cash",
                        "total_amount": 5000.500
                    },
                    {
                        "payment_mode": "card",
                        "total_amount": 3200.750
                    }
                ],
                "total_period": 8201.250
            },
            {
                "period": "2025-02",
                "payments_by_mode": [
                    {
                        "payment_mode": "transfer",
                        "total_amount": 12450.000
                    }
                ],
                "total_period": 12450.000
            }
        ]
    }
    ```
    """
    try:
        return PaymentTrackingService.get_traceable_payments_by_period_and_mode(db, year)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
