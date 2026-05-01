from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from decimal import Decimal
from datetime import datetime
from typing import List

from app.models.models import WasteManagement, Kpi, Anomaly
from app.schemas.waste_management_schemas import (
    WasteRecyclingRateMonthlyResponse,
    WasteRecyclingRateKpiDetailResponse
)


class WasteManagementService:
    """Service for calculating Waste Management KPI scores"""

    @staticmethod
    def detect_anomalies(db: Session, year: int = None):
        """
        Detect anomalies for WASTE.

        Two conditions are tracked:
        - total waste weight above the KPI target (lower is better)
        - recycling rate abnormally low

        Args:
            db: Database session
            year: Year to analyze (defaults to current year)
        """
        if year is None:
            year = datetime.now().year

        kpi = db.query(Kpi).filter(Kpi.code == "WASTE").first()
        if not kpi:
            raise ValueError("KPI with code WASTE not found")

        waste_data = WasteManagementService.get_monthly_recycling_rate(db, "WASTE", year)
        matched_anomalies = []
        seen_anomaly_ids = set()

        target_value = Decimal(str(kpi.target)) if kpi.target is not None else Decimal(0)
        recycling_rate_threshold = Decimal(10)

        for period in waste_data.monthly_scores:
            detected_weight = Decimal(str(period.total_weight_kg or 0))
            recycling_rate = Decimal(str(period.recycling_rate or 0))

            if target_value > 0 and detected_weight > target_value:
                gap = ((detected_weight - target_value) / target_value) * Decimal(100)

                if gap > Decimal(20):
                    severity = "critique"
                elif gap > Decimal(10):
                    severity = "haute"
                else:
                    severity = "moyenne"

                z_score = (detected_weight - target_value) / Decimal("5.0")
                description = (
                    f"Dépassement de {float(gap):.1f}% pour la période {period.month} "
                    f"(actuel: {float(detected_weight):.3f} kg, cible: {float(target_value):.3f} kg)"
                )

                existing_anomaly = db.query(Anomaly).filter(
                    Anomaly.kpi_id == kpi.id,
                    Anomaly.description.like(f"%{period.month}%")
                ).order_by(Anomaly.date_detected.desc()).first()

                if existing_anomaly:
                    if existing_anomaly.id not in seen_anomaly_ids:
                        matched_anomalies.append(existing_anomaly)
                        seen_anomaly_ids.add(existing_anomaly.id)
                else:
                    anomaly = Anomaly(
                        kpi_id=kpi.id,
                        detected_value=detected_weight,
                        expected_value=target_value,
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

            if period.total_weight_kg and recycling_rate < recycling_rate_threshold:
                gap = ((recycling_rate_threshold - recycling_rate) / recycling_rate_threshold) * Decimal(100)

                if gap > Decimal(20):
                    severity = "critique"
                elif gap > Decimal(10):
                    severity = "haute"
                else:
                    severity = "moyenne"

                z_score = (recycling_rate - recycling_rate_threshold) / Decimal("5.0")
                description = (
                    f"Performance faible de recyclage: écart de {float(gap):.1f}% pour la période {period.month} "
                    f"(taux: {float(recycling_rate):.1f}%, seuil d'alerte: {float(recycling_rate_threshold):.1f}%)"
                )

                existing_anomaly = db.query(Anomaly).filter(
                    Anomaly.kpi_id == kpi.id,
                    Anomaly.description.like(f"%{period.month}%")
                ).order_by(Anomaly.date_detected.desc()).first()

                if existing_anomaly:
                    if existing_anomaly.id not in seen_anomaly_ids:
                        matched_anomalies.append(existing_anomaly)
                        seen_anomaly_ids.add(existing_anomaly.id)
                else:
                    anomaly = Anomaly(
                        kpi_id=kpi.id,
                        detected_value=recycling_rate,
                        expected_value=recycling_rate_threshold,
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
