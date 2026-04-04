from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from typing import List

from app.models.models import PaymentTracking
from app.schemas.payment_tracking_schemas import (
    PaymentTrackingResponse,
    PaymentTrackingPeriodResponse,
    PaymentModeAmount
)


class PaymentTrackingService:
    """Service for payment tracking analysis"""

    @staticmethod
    def get_traceable_payments_by_period_and_mode(
        db: Session,
        year: int = None
    ) -> PaymentTrackingResponse:
        """
        Get traceable payments grouped by period and payment mode.
        
        Query:
        SELECT 
            DATE_FORMAT(period_date, '%Y-%m') AS period,
            payment_mode,
            SUM(amount_tnd) AS total_amount
        FROM payment_tracking
        WHERE is_traceable = 1 AND YEAR(period_date) = year
        GROUP BY period, payment_mode
        ORDER BY period
        
        Args:
            db: Database session
            year: Year to filter by (default: previous year)
        
        Returns:
            PaymentTrackingResponse with periods containing payments by mode
        """
        # Default to previous year if not provided
        if year is None:
            year = datetime.now().year - 1
        
        # Query payments grouped by period and payment_mode
        results = db.query(
            extract('year', PaymentTracking.period_date).label('year'),
            extract('month', PaymentTracking.period_date).label('month'),
            PaymentTracking.payment_mode,
            func.sum(PaymentTracking.amount_tnd).label('total_amount')
        ).filter(
            PaymentTracking.is_traceable == 1,
            extract('year', PaymentTracking.period_date) == year
        ).group_by(
            extract('year', PaymentTracking.period_date),
            extract('month', PaymentTracking.period_date),
            PaymentTracking.payment_mode
        ).order_by(
            extract('year', PaymentTracking.period_date),
            extract('month', PaymentTracking.period_date),
            PaymentTracking.payment_mode
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
                PaymentModeAmount(
                    payment_mode=row.payment_mode,
                    total_amount=float(row.total_amount or 0)
                )
            )
        
        # Convert to periods list with totals
        periods_list = []
        for period_str in sorted(periods_dict.keys()):
            payments = periods_dict[period_str]
            total_period = sum(p.total_amount for p in payments)
            
            periods_list.append(
                PaymentTrackingPeriodResponse(
                    period=period_str,
                    payments_by_mode=payments,
                    total_period=total_period
                )
            )
        
        return PaymentTrackingResponse(periods=periods_list)
