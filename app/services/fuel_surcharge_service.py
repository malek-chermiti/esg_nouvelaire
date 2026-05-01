from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from decimal import Decimal
from datetime import datetime
from typing import List

from app.models.models import FuelSurcharge, Kpi, Anomaly
from app.services.ai_service import AIService
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

    @staticmethod
    def detect_monthly_anomalies(db: Session, year: int):
        """
        Detect anomalies in monthly Fuel Surcharge amounts.
        
        Compares total_amount_tnd to kpi_target for each month.
        Creates anomalies if actual value exceeds target by more than 5%.
        Direction: LOWER (anomaly if actual > target)
        
        Args:
            db: Database session
            year: Year to analyze
        """
        
        # Get KPI details
        kpi = db.query(Kpi).filter(Kpi.code == "fuel_surcharge").first()
        if not kpi:
            raise ValueError("KPI with code fuel_surcharge not found")
        
        # Get monthly Fuel Surcharge data
        monthly_scores = FuelSurchargeService.get_monthly_fuel_surcharge_score(db, "fuel_surcharge", year).monthly_scores
        matched_anomalies = []
        seen_anomaly_ids = set()
        
        for score in monthly_scores:
            detected_value = score.total_amount_tnd
            expected_value = score.kpi_target
            
            # Calculate gap percentage: ((actual - target) / target) * 100
            if expected_value > 0:
                gap = ((detected_value - expected_value) / expected_value) * 100
            else:
                gap = 0
            
            # Check if gap exceeds 5% threshold (LOWER direction: anomaly if actual > target)
            if gap > 5:
                # Determine severity
                if gap > 20:
                    severity = "critique"
                elif gap > 10:
                    severity = "haute"
                else:
                    severity = "moyenne"
                
                # Calculate z-score (using default std_dev = 5.0)
                std_dev = 5.0
                z_score = (detected_value - expected_value) / std_dev if std_dev > 0 else 0
                
                # Create anomaly description
                description = f"Dépassement de {gap:.1f}% du seuil Fuel Surcharge pour le mois {score.month}"
                
                # Check if anomaly already exists for this KPI and period
                existing_anomaly = db.query(Anomaly).filter(
                    Anomaly.kpi_id == kpi.id,
                    Anomaly.description.like(f"%{score.month}%")
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
                    
                    try:
                        AIService.generate_recommendation(db, anomaly)
                    except Exception as e:
                        pass  # Continue even if AI fails
                    
                    matched_anomalies.append(anomaly)
                    seen_anomaly_ids.add(anomaly.id)

        return matched_anomalies
