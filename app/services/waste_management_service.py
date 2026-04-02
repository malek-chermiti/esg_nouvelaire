from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from decimal import Decimal
from datetime import datetime
from typing import List

from app.models.models import WasteManagement, Kpi
from app.schemas.waste_management_schemas import (
    WasteRecyclingRateMonthlyResponse,
    WasteRecyclingRateKpiDetailResponse
)


class WasteManagementService:
    """Service for calculating Waste Management KPI scores"""

    @staticmethod
    def get_monthly_recycling_rate(
        db: Session,
        kpi_code: str = "WASTE",
        year: int = None
    ) -> WasteRecyclingRateKpiDetailResponse:
        """
        Calculate monthly recycling rate KPI score.
        
        Formula: (sum(weight_kg where is_recycled=1) / sum(weight_kg)) * 100
        
        Args:
            db: Database session
            kpi_code: KPI code (default: "recycling_rate")
            year: Filter by year (optional)
        
        Returns:
            WasteRecyclingRateKpiDetailResponse with monthly recycling rates
        """
        
        # Get KPI details
        kpi = db.query(Kpi).filter(Kpi.code == kpi_code).first()
        if not kpi:
            raise ValueError(f"KPI with code {kpi_code} not found")
        
        # Build query for total waste weight grouped by month
        query = db.query(
            extract('year', WasteManagement.period_date).label('year'),
            extract('month', WasteManagement.period_date).label('month'),
            func.sum(WasteManagement.weight_kg).label('total_weight_kg'),
            func.sum(
                func.if_(WasteManagement.is_recycled == 1, WasteManagement.weight_kg, 0)
            ).label('recycled_weight_kg')
        ).group_by(
            extract('year', WasteManagement.period_date),
            extract('month', WasteManagement.period_date)
        ).order_by(
            extract('year', WasteManagement.period_date).desc(),
            extract('month', WasteManagement.period_date).desc()
        )
        
        # Filter by year if provided
        if year:
            query = query.filter(
                extract('year', WasteManagement.period_date) == year
            )
        
        monthly_data = query.all()
        
        # Calculate recycling rates and build response
        monthly_scores = []
        target = Decimal(str(kpi.target)) if kpi.target else Decimal(1)  # Avoid division by zero
        
        for row in monthly_data:
            year_val = int(row.year)
            month_val = int(row.month)
            total_weight = Decimal(str(row.total_weight_kg)) if row.total_weight_kg else Decimal(0)
            recycled_weight = Decimal(str(row.recycled_weight_kg)) if row.recycled_weight_kg else Decimal(0)
            
            # Calculate recycling rate: (recycled_weight / total_weight) * 100
            recycling_rate = (recycled_weight / total_weight) * 100 if total_weight > 0 else Decimal(0)
            
            # Calculate score: (recycling_rate / target) * 100
            score = (recycling_rate / target) * 100 if target > 0 else Decimal(0)
            
            month_str = f"{year_val:04d}-{month_val:02d}"
            
            monthly_scores.append(
                WasteRecyclingRateMonthlyResponse(
                    month=month_str,
                    total_weight_kg=total_weight,
                    recycled_weight_kg=recycled_weight,
                    recycling_rate=recycling_rate,
                    kpi_target=target,
                    score=score
                )
            )
        
        return WasteRecyclingRateKpiDetailResponse(
            kpi_code=kpi.code,
            kpi_name=kpi.name,
            unit=kpi.unit,
            monthly_scores=monthly_scores
        )
