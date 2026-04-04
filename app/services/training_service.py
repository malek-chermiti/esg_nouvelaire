from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime

from app.models.models import Training
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
