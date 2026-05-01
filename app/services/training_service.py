from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from decimal import Decimal

from app.models.models import Training, Kpi, Anomaly
from app.schemas.training_schemas import (
    TrainingHoursByQuarter,
    TrainingHoursPerQuarterResponse
)


class TrainingService:
    """Service for training management and statistics"""

    @staticmethod
    def get_training_hours_per_quarter(
        db: Session,
        year: int
    ) -> TrainingHoursPerQuarterResponse:
        """
        Calculate training hours by quarter for a given year.
        
        Q1: January - March (months 1-3)
        Q2: April - June (months 4-6)
        Q3: July - September (months 7-9)
        Q4: October - December (months 10-12)
        
        Args:
            db: Database session
            year: Year to filter (e.g., 2024)
        
        Returns:
            TrainingHoursPerQuarterResponse with quarterly breakdown
        """
        
        # Query all training data for the year
        trainings = db.query(Training).filter(
            extract('year', Training.training_date) == year
        ).all()
        
        # Initialize quarters
        quarters_data = {
            1: {'name': f'Q1 {year}', 'hours': 0},
            2: {'name': f'Q2 {year}', 'hours': 0},
            3: {'name': f'Q3 {year}', 'hours': 0},
            4: {'name': f'Q4 {year}', 'hours': 0},
        }
        
        total_hours_year = 0
        
        # Calculate hours by quarter
        for training in trainings:
            month = training.training_date.month
            hours = float(training.hours) if training.hours else 0
            
            # Determine quarter
            if 1 <= month <= 3:
                quarter = 1
            elif 4 <= month <= 6:
                quarter = 2
            elif 7 <= month <= 9:
                quarter = 3
            else:
                quarter = 4
            
            quarters_data[quarter]['hours'] += hours
            total_hours_year += hours
        
        # Build response
        quarters_list = [
            TrainingHoursByQuarter(
                quarter=quarters_data[q]['name'],
                total_hours=quarters_data[q]['hours']
            )
            for q in sorted(quarters_data.keys())
        ]
        
        return TrainingHoursPerQuarterResponse(
            year=year,
            total_hours_year=total_hours_year,
            quarters=quarters_list
        )

    @staticmethod
    def validate_year(year: int) -> bool:
        """Validate year is reasonable"""
        current_year = datetime.now().year
        if year < 2000 or year > current_year + 1:
            raise ValueError(f"Year must be between 2000 and {current_year + 1}")
        return True

    @staticmethod
    def detect_quarterly_anomalies(db: Session, year: int):
        """
        Detect anomalies in quarterly training hours (FORMATION).
        
        Compares total_hours for each quarter to quarterly target (annual_target / 4).
        Creates anomalies if actual value is below target by more than 5%.
        Direction: HIGHER (anomaly if actual < target)
        
        Args:
            db: Database session
            year: Year to analyze
        """
        
        # Get KPI details
        kpi = db.query(Kpi).filter(Kpi.code == "FORMATION").first()
        if not kpi:
            raise ValueError("KPI with code FORMATION not found")
        
        # Get quarterly training data
        training_data = TrainingService.get_training_hours_per_quarter(db, year)
        annual_target = Decimal(str(kpi.target)) if kpi.target is not None else Decimal(0)
        quarterly_target = (annual_target / Decimal(4)) if annual_target > 0 else Decimal(0)

        matched_anomalies = []
        seen_anomaly_ids = set()

        for quarter in training_data.quarters:
            detected_value = Decimal(str(quarter.total_hours))
            expected_value = quarterly_target

            # Calculate gap percentage: ((target - actual) / target) * 100 for HIGHER direction
            if expected_value > 0:
                gap = ((expected_value - detected_value) / expected_value) * 100
            else:
                gap = Decimal(0)

            # Check if gap exceeds 5% threshold (HIGHER direction: anomaly if actual < target)
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
                description = f"Écart de {float(gap):.1f}% sous le seuil de formation pour {quarter.quarter} (cible: {float(expected_value):.1f}h, actuel: {float(detected_value):.1f}h)"

                # Check if anomaly already exists for this KPI and quarter
                existing_anomaly = db.query(Anomaly).filter(
                    Anomaly.kpi_id == kpi.id,
                    Anomaly.description.like(f"%{quarter.quarter}%")
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
