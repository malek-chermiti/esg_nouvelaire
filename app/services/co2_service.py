from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from decimal import Decimal
from datetime import datetime
from typing import List

from app.models.models import Co2Emission, Kpi, Anomaly
from app.schemas.co2_schemas import (
    Co2MonthlyScoreResponse,
    Co2KpiDetailResponse,
    Co2ByRouteResponse,
    Co2RouteConsumptionResponse
)


class Co2Service:
    """Service for calculating CO2 KPI scores"""

    @staticmethod
    def get_monthly_co2_score(
        db: Session,
        kpi_code: str = "co2",
        year: int = None
    ) -> Co2KpiDetailResponse:
        """
        Calculate monthly CO2 KPI score.
        
        Formula: (sum(co2_kg) / kpi_target) * 100
        
        Args:
            db: Database session
            kpi_code: KPI code (default: "C02")
            year: Filter by year (optional)
        
        Returns:
            Co2KpiDetailResponse with monthly scores
        """
        
        # Get KPI details
        kpi = db.query(Kpi).filter(Kpi.code == kpi_code).first()
        if not kpi:
            raise ValueError(f"KPI with code {kpi_code} not found")
        
        # Build query for CO2 emissions grouped by month
        query = db.query(
            extract('year', Co2Emission.period_date).label('year'),
            extract('month', Co2Emission.period_date).label('month'),
            func.sum(Co2Emission.co2_kg).label('total_co2_kg')
        ).group_by(
            extract('year', Co2Emission.period_date),
            extract('month', Co2Emission.period_date)
        ).order_by(
            extract('year', Co2Emission.period_date).desc(),
            extract('month', Co2Emission.period_date).desc()
        )
        
        # Filter by year if provided
        if year:
            query = query.filter(
                extract('year', Co2Emission.period_date) == year
            )
        
        monthly_data = query.all()
        
        # Calculate scores and build response
        monthly_scores = []
        for row in monthly_data:
            year_val = int(row.year)
            month_val = int(row.month)
            total_co2 = Decimal(str(row.total_co2_kg)) if row.total_co2_kg else Decimal(0)
            target = Decimal(str(kpi.target)) if kpi.target else Decimal(1)  # Avoid division by zero
            
            # Calculate score: (sum(co2) / target) * 100, capped at 100
            score = (total_co2 / target) * 100 if target > 0 else Decimal(0)
            score = min(score, Decimal(100))  # Cap at 100
            
            month_str = f"{year_val:04d}-{month_val:02d}"
            
            monthly_scores.append(
                Co2MonthlyScoreResponse(
                    month=month_str,
                    total_co2_kg=total_co2,
                    kpi_target=target,
                    score=score
                )
            )
        
        return Co2KpiDetailResponse(
            kpi_code=kpi.code,
            kpi_name=kpi.name,
            unit=kpi.unit,
            monthly_scores=monthly_scores
        )

    @staticmethod
    def get_co2_by_route(
        db: Session
    ) -> Co2RouteConsumptionResponse:
        """
        Get CO2 consumption grouped by route for entire database.
        
        Formula: sum(co2_kg) by route, converted to tonnes
        
        Args:
            db: Database session
        
        Returns:
            Co2RouteConsumptionResponse with consumption by route
        """
        
        # Build query for CO2 emissions grouped by route
        query = db.query(
            Co2Emission.route,
            func.sum(Co2Emission.co2_kg).label('total_co2_kg')
        ).group_by(
            Co2Emission.route
        ).order_by(
            func.sum(Co2Emission.co2_kg).desc()
        )
        
        route_data = query.all()
        
        # Calculate consumption by route and build response
        routes = []
        total_co2 = Decimal(0)
        
        for row in route_data:
            co2_kg = Decimal(str(row.total_co2_kg)) if row.total_co2_kg else Decimal(0)
            # Convert kg to tonnes (1 tonne = 1000 kg)
            co2_tonnes = co2_kg / Decimal(1000)
            total_co2 += co2_kg
            
            routes.append(
                Co2ByRouteResponse(
                    route=row.route,
                    co2_tonnes=co2_tonnes
                )
            )
        
        # Convert total to tonnes
        total_co2_tonnes = total_co2 / Decimal(1000)
        
        return Co2RouteConsumptionResponse(
            title="Consommation Carburant par Route",
            unit="tonnes",
            total_co2_tonnes=total_co2_tonnes,
            by_route=routes
        )

    @staticmethod
    def detect_monthly_anomalies(db: Session, year: int):
        """
        Detect anomalies in monthly CO2 emissions.
        
        Compares total_co2_kg to kpi_target for each month.
        Creates anomalies if actual value exceeds target by more than 5%.
        Direction: LOWER (anomaly if actual > target)
        
        Args:
            db: Database session
            year: Year to analyze
        """
        
        # Get KPI details
        kpi = db.query(Kpi).filter(Kpi.code == "CO2").first()
        if not kpi:
            raise ValueError("KPI with code CO2 not found")
        
        # Get monthly CO2 data
        monthly_scores = Co2Service.get_monthly_co2_score(db, "CO2", year).monthly_scores
        created_anomalies = []
        
        for score in monthly_scores:
            detected_value = score.total_co2_kg
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
                description = f"Dépassement de {gap:.1f}% du seuil CO2 pour le mois {score.month}"
                
                # Check if anomaly already exists for this KPI and period
                existing_anomaly = db.query(Anomaly).filter(
                    Anomaly.kpi_id == kpi.id,
                    Anomaly.description == description,
                    Anomaly.status == "NEW"
                ).first()
                
                if not existing_anomaly:
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
                    created_anomalies.append(anomaly)

        return created_anomalies
