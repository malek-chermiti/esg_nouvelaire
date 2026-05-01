from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from decimal import Decimal
from typing import List

from app.models.models import AviationLicense, Kpi, Anomaly
from app.services.ai_service import AIService
from app.schemas.aviation_license_schemas import (
    AviationLicenseResponse,
    AviationLicensePeriodResponse,
    LicenseTypeAmount
)


class AviationLicenseService:
    """Service for aviation license analysis"""

    @staticmethod
    def detect_anomalies(db: Session, year: int = None):
        """
        Detect anomalies for AVIA_ACTIVE.

        The service compares each period against the previous one and computes a
        compliance score based on the license types that should still be present.
        Missing license types or significant cost drops reduce the score below 100%.

        Args:
            db: Database session
            year: Year to analyze (defaults to current year)
        """
        if year is None:
            year = datetime.now().year

        kpi = db.query(Kpi).filter(Kpi.code == "AVIA_ACTIVE").first()
        if not kpi:
            raise ValueError("KPI with code AVIA_ACTIVE not found")

        aviation_data = AviationLicenseService.get_active_pending_licenses_by_period_and_type(db, year)
        matched_anomalies = []
        seen_anomaly_ids = set()

        previous_period_costs = None

        for period in aviation_data.periods:
            current_period_costs = {
                license_item.license_type: Decimal(str(license_item.total_cost or 0))
                for license_item in period.licenses_by_type
            }

            if previous_period_costs:
                previous_license_types = sorted(previous_period_costs.keys())
                if previous_license_types:
                    compliance_ratios = []
                    missing_license_types = []
                    cost_drops = []

                    for license_type in previous_license_types:
                        previous_cost = previous_period_costs[license_type]
                        current_cost = current_period_costs.get(license_type)

                        if current_cost is None:
                            compliance_ratios.append(Decimal(0))
                            missing_license_types.append(license_type)
                            continue

                        if previous_cost > 0:
                            ratio = min(current_cost, previous_cost) / previous_cost
                        else:
                            ratio = Decimal(1)

                        compliance_ratios.append(ratio)

                        if current_cost < previous_cost:
                            cost_drops.append(license_type)

                    if compliance_ratios:
                        compliance_score = sum(compliance_ratios) / Decimal(len(compliance_ratios)) * Decimal(100)
                        detected_value = compliance_score
                        expected_value = Decimal(str(kpi.target)) if kpi.target is not None else Decimal(100)

                        if expected_value > 0:
                            gap = ((expected_value - detected_value) / expected_value) * Decimal(100)
                        else:
                            gap = Decimal(0)

                        if gap > Decimal(0):
                            if gap > Decimal(20):
                                severity = "critique"
                            elif gap > Decimal(10):
                                severity = "haute"
                            else:
                                severity = "moyenne"

                            z_score = (detected_value - expected_value) / Decimal("5.0")

                            description_parts = [
                                f"Écart de {float(gap):.1f}% pour la période {period.period}"
                            ]
                            if missing_license_types:
                                description_parts.append(
                                    f"licences manquantes: {', '.join(missing_license_types)}"
                                )
                            if cost_drops:
                                description_parts.append(
                                    f"coûts en baisse: {', '.join(cost_drops)}"
                                )

                            description = " - ".join(description_parts)

                            existing_anomaly = db.query(Anomaly).filter(
                                Anomaly.kpi_id == kpi.id,
                                Anomaly.description.like(f"%{period.period}%")
                            ).order_by(Anomaly.date_detected.desc()).first()

                            if existing_anomaly:
                                if existing_anomaly.id not in seen_anomaly_ids:
                                    # Generate recommendation if missing
                                    from app.models.models import Recommendation
                                    has_rec = db.query(Recommendation).filter(Recommendation.anomaly_id == existing_anomaly.id).first()
                                    if not has_rec:
                                        try:
                                            AIService.generate_recommendation(db, existing_anomaly)
                                        except Exception as e:
                                            pass
                                    matched_anomalies.append(existing_anomaly)
                                    seen_anomaly_ids.add(existing_anomaly.id)
                            else:
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
                                
                                try:
                                    AIService.generate_recommendation(db, anomaly)
                                except Exception as e:
                                    pass  # Continue even if AI fails
                                
                                matched_anomalies.append(anomaly)
                                seen_anomaly_ids.add(anomaly.id)

            previous_period_costs = current_period_costs

        return matched_anomalies


    @staticmethod
    def get_active_pending_licenses_by_period_and_type(
        db: Session,
        year: int = None
    ) -> AviationLicenseResponse:
        """
        Get active and pending aviation licenses grouped by period and license type.
        
        Query:
        SELECT 
            DATE_FORMAT(period_date, '%Y-%m') AS period,
            license_type,
            SUM(cost_tnd) AS total_cost
        FROM aviation_license
        WHERE status IN ('ACTIVE', 'PENDING') AND YEAR(period_date) = year
        GROUP BY period, license_type
        ORDER BY period, license_type
        
        Args:
            db: Database session
            year: Year to filter by (default: previous year)
        
        Returns:
            AviationLicenseResponse with periods containing licenses by type
        """
        # Default to previous year if not provided
        if year is None:
            year = datetime.now().year - 1
        
        # Query aviation licenses grouped by period and license_type
        results = db.query(
            extract('year', AviationLicense.period_date).label('year'),
            extract('month', AviationLicense.period_date).label('month'),
            AviationLicense.license_type,
            func.sum(AviationLicense.cost_tnd).label('total_cost')
        ).filter(
            AviationLicense.status.in_(['ACTIVE', 'PENDING']),
            extract('year', AviationLicense.period_date) == year
        ).group_by(
            extract('year', AviationLicense.period_date),
            extract('month', AviationLicense.period_date),
            AviationLicense.license_type
        ).order_by(
            extract('year', AviationLicense.period_date),
            extract('month', AviationLicense.period_date),
            AviationLicense.license_type
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
                LicenseTypeAmount(
                    license_type=row.license_type,
                    total_cost=float(row.total_cost or 0)
                )
            )
        
        # Convert to periods list with totals
        periods_list = []
        for period_str in sorted(periods_dict.keys()):
            licenses = periods_dict[period_str]
            total_period = sum(l.total_cost for l in licenses)
            
            periods_list.append(
                AviationLicensePeriodResponse(
                    period=period_str,
                    licenses_by_type=licenses,
                    total_period=total_period
                )
            )
        
        return AviationLicenseResponse(
            year=year,
            periods=periods_list
        )
