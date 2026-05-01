from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from typing import List
from decimal import Decimal

from app.models.models import TaxObligation, Kpi, Anomaly
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

    @staticmethod
    def detect_monthly_anomalies(db: Session, year: int):
        """
        Detect anomalies in monthly Tax Obligations.
        
        Compares total_period to kpi_target for each period.
        Creates anomalies if actual value exceeds target by more than 5%.
        Direction: LOWER (anomaly if actual > target)
        
        Args:
            db: Database session
            year: Year to analyze
        """
        
        # Get KPI details
        kpi = db.query(Kpi).filter(Kpi.code == "TAX_OBLIGAT").first()
        if not kpi:
            raise ValueError("KPI with code TAX_OBLIGAT not found")
        
        # Get tax obligation data
        tax_data = TaxObligationService.get_tax_obligations_by_period_and_type(db, year)
        
        matched_anomalies = []
        seen_anomaly_ids = set()

        for period in tax_data.periods:
            detected_value = Decimal(str(period.total_period))
            expected_value = Decimal(str(kpi.target)) if kpi.target is not None else Decimal(0)

            # Calculate gap percentage: ((actual - target) / target) * 100
            if expected_value > 0:
                gap = ((detected_value - expected_value) / expected_value) * 100
            else:
                gap = Decimal(0)

            # Check if gap exceeds 5% threshold (LOWER direction: anomaly if actual > target)
            if gap > Decimal(5):
                # Determine severity
                if gap > Decimal(20):
                    severity = "critique"
                elif gap > Decimal(10):
                    severity = "haute"
                else:
                    severity = "moyenne"

                # Calculate z-score (using default std_dev = 5.0)
                std_dev = Decimal("5.0")
                z_score = (detected_value - expected_value) / std_dev if std_dev > 0 else Decimal(0)

                # Create anomaly description
                description = f"Dépassement de {float(gap):.1f}% du seuil Tax Obligation pour la période {period.period}"

                # Check if anomaly already exists for this KPI and period
                existing_anomaly = db.query(Anomaly).filter(
                    Anomaly.kpi_id == kpi.id,
                    Anomaly.description.like(f"%{period.period}%")
                ).order_by(Anomaly.date_detected.desc()).first()

                if existing_anomaly:
                    if existing_anomaly.id not in seen_anomaly_ids:
                        matched_anomalies.append(existing_anomaly)
                        seen_anomaly_ids.add(existing_anomaly.id)
                else:
                    # Create and save anomaly
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
                    matched_anomalies.append(anomaly)
                    seen_anomaly_ids.add(anomaly.id)

        return matched_anomalies
