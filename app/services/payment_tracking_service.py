from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from decimal import Decimal
from typing import List

from app.models.models import PaymentTracking, Kpi, Anomaly
from app.schemas.payment_tracking_schemas import (
    PaymentTrackingResponse,
    PaymentTrackingPeriodResponse,
    PaymentModeAmount
)


class PaymentTrackingService:
    """Service for payment tracking analysis"""

    @staticmethod
    def detect_anomalies(db: Session, year: int = None):
        """
        Detect anomalies for PAYMENT_TRACE.

        The detected value is the percentage of traceable payment amount over
        the total payment amount for each period.

        Args:
            db: Database session
            year: Year to analyze (defaults to current year)
        """
        if year is None:
            year = datetime.now().year

        kpi = db.query(Kpi).filter(Kpi.code == "PAYMENT_TRACE").first()
        if not kpi:
            raise ValueError("KPI with code PAYMENT_TRACE not found")

        results = db.query(
            extract('year', PaymentTracking.payment_date).label('year'),
            extract('month', PaymentTracking.payment_date).label('month'),
            func.sum(PaymentTracking.amount_tnd).label('total_amount'),
            func.sum(
                func.if_(PaymentTracking.is_traceable == 1, PaymentTracking.amount_tnd, 0)
            ).label('traceable_amount')
        ).filter(
            extract('year', PaymentTracking.payment_date) == year
        ).group_by(
            extract('year', PaymentTracking.payment_date),
            extract('month', PaymentTracking.payment_date)
        ).order_by(
            extract('year', PaymentTracking.payment_date),
            extract('month', PaymentTracking.payment_date)
        ).all()

        created_anomalies = []

        for row in results:
            year_val = int(row.year)
            month_val = int(row.month)
            period_str = f"{year_val:04d}-{month_val:02d}"

            total_amount = Decimal(str(row.total_amount or 0))
            traceable_amount = Decimal(str(row.traceable_amount or 0))

            traceability_rate = (
                (traceable_amount / total_amount) * Decimal(100)
                if total_amount > 0 else Decimal(0)
            )

            expected_value = Decimal(100)
            detected_value = traceability_rate
            gap = ((expected_value - detected_value) / expected_value) * Decimal(100)

            if gap > Decimal(0):
                if gap > Decimal(20):
                    severity = "critique"
                elif gap > Decimal(10):
                    severity = "haute"
                else:
                    severity = "moyenne"

                z_score = (detected_value - expected_value) / Decimal("5.0")
                non_traceable_amount = total_amount - traceable_amount

                description = (
                    f"Paiements traçables à {float(traceability_rate):.1f}% pour {period_str} "
                    f"(traçable: {float(traceable_amount):.3f}, non traçable: {float(non_traceable_amount):.3f})"
                )

                existing_anomaly = db.query(Anomaly).filter(
                    Anomaly.kpi_id == kpi.id,
                    Anomaly.description == description,
                    Anomaly.status == "NEW"
                ).first()

                if not existing_anomaly:
                    anomaly = Anomaly(
                        kpi_id=kpi.id,
                        detected_value=detected_value,
                        expected_value=expected_value,
                        z_score=z_score,
                        severity=severity,
                        description=description,
                        status="NEW",
                        date_detected=datetime.now()
                    )

                    db.add(anomaly)
                    db.commit()
                    db.refresh(anomaly)
                    created_anomalies.append(anomaly)

        return created_anomalies


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
