from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from decimal import Decimal
from datetime import datetime
from typing import List

from app.models.models import FuelSurcharge, Kpi
from app.schemas.fuel_surcharge_schemas import (
    FuelSurchargeMonthlyScoreResponse,
    FuelSurchargeKpiDetailResponse
)


class FuelSurchargeService:
    """Service for calculating Fuel Surcharge KPI scores"""

    @staticmethod
    def get_monthly_fuel_surcharge_score(
        db: Session,
        kpi_code: str = "fuel_surcharge",
        year: int = None
    ) -> FuelSurchargeKpiDetailResponse:
        """
        Calculate monthly Fuel Surcharge KPI score.
        
        Formula: (sum(amount_tnd) / kpi_target) * 100
        
        Args:
            db: Database session
            kpi_code: KPI code (default: "fuel_surcharge")
            year: Filter by year (optional)
        
        Returns:
            FuelSurchargeKpiDetailResponse with monthly scores
        """
        
        # Get KPI details
        kpi = db.query(Kpi).filter(Kpi.code == kpi_code).first()
        if not kpi:
            raise ValueError(f"KPI with code {kpi_code} not found")
        
        # Build query for Fuel Surcharge amounts grouped by month
        query = db.query(
            extract('year', FuelSurcharge.period_date).label('year'),
            extract('month', FuelSurcharge.period_date).label('month'),
            func.sum(FuelSurcharge.amount_tnd).label('total_amount_tnd')
        ).group_by(
            extract('year', FuelSurcharge.period_date),
            extract('month', FuelSurcharge.period_date)
        ).order_by(
            extract('year', FuelSurcharge.period_date).desc(),
            extract('month', FuelSurcharge.period_date).desc()
        )
        
        # Filter by year if provided
        if year:
            query = query.filter(
                extract('year', FuelSurcharge.period_date) == year
            )
        
        monthly_data = query.all()
        
        # Calculate scores and build response
        monthly_scores = []
        for row in monthly_data:
            year_val = int(row.year)
            month_val = int(row.month)
            total_amount = Decimal(str(row.total_amount_tnd)) if row.total_amount_tnd else Decimal(0)
            target = Decimal(str(kpi.target)) if kpi.target else Decimal(1)  # Avoid division by zero
            
            # Calculate score: (sum(amount) / target) * 100, capped at 100
            score = (total_amount / target) * 100 if target > 0 else Decimal(0)
            score = min(score, Decimal(100))  # Cap at 100
            
            month_str = f"{year_val:04d}-{month_val:02d}"
            
            monthly_scores.append(
                FuelSurchargeMonthlyScoreResponse(
                    month=month_str,
                    total_amount_tnd=total_amount,
                    kpi_target=target,
                    score=score
                )
            )
        
        return FuelSurchargeKpiDetailResponse(
            kpi_code=kpi.code,
            kpi_name=kpi.name,
            unit=kpi.unit,
            monthly_scores=monthly_scores
        )
