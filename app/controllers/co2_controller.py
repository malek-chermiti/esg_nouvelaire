from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.co2_service import Co2Service
from app.schemas.co2_schemas import (
    Co2KpiDetailResponse,
    Co2RouteConsumptionResponse
)


router = APIRouter(
    prefix="/api/kpi/co2",
    tags=["Co2 KPI"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/monthly-score",
    response_model=Co2KpiDetailResponse,
    summary="Get monthly Co2 KPI score",
    description="Calculate and retrieve monthly CO2 KPI scores (score = (sum(co2_kg) / target) * 100)"
)
def get_monthly_co2_score(
    year: Optional[int] = None,
    kpi_code: str = "co2",
    db: Session = Depends(get_db)
):
    """
    Get monthly CO2 KPI scores by month.
    
    - **year**: Optional year filter (YYYY format)
    - **kpi_code**: KPI code (default: C02)
    - **Returns**: Monthly scores with CO2 totals and calculated percentages
    
    Example response:
    ```
    {
        "kpi_code": "C02",
        "kpi_name": "CO2 Emissions",
        "unit": "kg",
        "monthly_scores": [
            {
                "month": "2026-04",
                "total_co2_kg": 5000,
                "kpi_target": 10000,
                "score": 50.0
            }
        ]
    }
    ```
    """
    try:
        return Co2Service.get_monthly_co2_score(
            db=db,
            kpi_code=kpi_code,
            year=year
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/by-route",
    response_model=Co2RouteConsumptionResponse,
    summary="Get CO2 consumption by route",
    description="Get total CO2 consumption grouped by route in tonnes for entire database"
)
def get_co2_by_route(
    db: Session = Depends(get_db)
):
    """
    Get CO2 consumption by route from entire database.
    
    - **Returns**: CO2 consumption per route in tonnes, sorted by highest consumption first
    
    Example response:
    ```
    {
        "title": "Consommation Carburant par Route",
        "unit": "tonnes",
        "total_co2_tonnes": 1200.456,
        "by_route": [
            {
                "route": "TN-001",
                "co2_tonnes": 500.123
            },
            {
                "route": "TN-002",
                "co2_tonnes": 300.456
            }
        ]
    }
    ```
    """
    try:
        return Co2Service.get_co2_by_route(
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
