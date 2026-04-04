from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from typing import List

from app.models.models import TaxObligation
from app.schemas.tax_obligation_schemas import (
    TaxObligationResponse,
    TaxObligationPeriodResponse,
    TaxTypeAmount
)


class TaxObligationService:
    """Service for tax obligation analysis"""

    @staticmethod
    def get_tax_obligations_by_period_and_type(
        db: Session,
        year: int = None
    ) -> TaxObligationResponse:
        """
        Get tax obligations grouped by period and tax type.
        
        Query:
        SELECT 
            DATE_FORMAT(period_start, '%Y-%m') AS period,
            tax_type,
            SUM(amount_tnd) AS total_amount
        FROM tax_obligation
        WHERE YEAR(period_start) = year
        GROUP BY period, tax_type
        ORDER BY period, tax_type
        
        Args:
            db: Database session
            year: Year to filter by (default: previous year)
        
        Returns:
            TaxObligationResponse with periods containing taxes by type
        """
        # Default to previous year if not provided
        if year is None:
            year = datetime.now().year - 1
        
        # Query tax obligations grouped by period and tax_type
        results = db.query(
            extract('year', TaxObligation.period_start).label('year'),
            extract('month', TaxObligation.period_start).label('month'),
            TaxObligation.tax_type,
            func.sum(TaxObligation.amount_tnd).label('total_amount')
        ).filter(
            extract('year', TaxObligation.period_start) == year
        ).group_by(
            extract('year', TaxObligation.period_start),
            extract('month', TaxObligation.period_start),
            TaxObligation.tax_type
        ).order_by(
            extract('year', TaxObligation.period_start),
            extract('month', TaxObligation.period_start),
            TaxObligation.tax_type
        ).all()
        
        # Organize data by period
        periods_dict = {}
        
        for row in results:
            year_val = int(row.year)
            month = int(row.month)
            period_str = f"{year_val:04d}-{month:02d}"
            
            if period_str not in periods_dict:
                periods_dict[period_str] = []
            
            periods_dict[period_str].append(
                TaxTypeAmount(
                    tax_type=row.tax_type,
                    total_amount=float(row.total_amount or 0)
                )
            )
        
        # Convert to periods list with totals
        periods_list = []
        for period_str in sorted(periods_dict.keys()):
            taxes = periods_dict[period_str]
            total_period = sum(t.total_amount for t in taxes)
            
            periods_list.append(
                TaxObligationPeriodResponse(
                    period=period_str,
                    taxes_by_type=taxes,
                    total_period=total_period
                )
            )
        
        return TaxObligationResponse(
            year=year,
            periods=periods_list
        )
