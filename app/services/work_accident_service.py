from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from typing import List

from app.models.models import WorkAccident, Employee
from app.schemas.work_accident_schemas import (
    LTIRMonthlyResponse,
    LTIRDetailResponse
)


class WorkAccidentService:
    """Service for LTIR (Lost Time Injury Rate) calculations"""
    
    # Constants
    HOURS_PER_EMPLOYEE_PER_MONTH = 166
    LTIR_MULTIPLIER = 1_000_000

    @staticmethod
    def get_active_employees_count(db: Session) -> int:
        """
        Count the number of active employees.
        
        Args:
            db: Database session
        
        Returns:
            Number of active employees
        """
        return db.query(func.count(Employee.id)).filter(
            Employee.is_active == 1
        ).scalar() or 0

    @staticmethod
    def get_lost_time_accidents_by_month(
        db: Session,
        month: int,
        year: int
    ) -> int:
        """
        Count lost-time accidents for a specific month and year.
        
        Args:
            db: Database session
            month: Month number (1-12)
            year: Year
        
        Returns:
            Number of lost-time accidents
        """
        return db.query(func.count(WorkAccident.id)).filter(
            WorkAccident.is_lost_time == 1,
            extract('month', WorkAccident.accident_date) == month,
            extract('year', WorkAccident.accident_date) == year
        ).scalar() or 0

    @staticmethod
    def calculate_hours_worked(nb_employees: int) -> float:
        """
        Calculate total hours worked by employees.
        
        Formula: heures = nb_employees × 166
        
        Args:
            nb_employees: Number of active employees
        
        Returns:
            Total hours worked
        """
        return float(nb_employees * WorkAccidentService.HOURS_PER_EMPLOYEE_PER_MONTH)

    @staticmethod
    def calculate_ltir(nb_accidents: int, hours_worked: float) -> float:
        """
        Calculate Lost Time Injury Rate (LTIR).
        
        Formula: LTIR = (nb_accidents × 1,000,000) / heures
        
        Args:
            nb_accidents: Number of lost-time accidents
            hours_worked: Total hours worked
        
        Returns:
            LTIR value (or 0 if hours_worked is 0)
        """
        if hours_worked == 0:
            return 0.0
        
        ltir = (nb_accidents * WorkAccidentService.LTIR_MULTIPLIER) / hours_worked
        return float(ltir)

    @staticmethod
    def get_ltir_by_month(
        db: Session,
        year: int = None
    ) -> LTIRDetailResponse:
        """
        Calculate LTIR for each month of the year.
        
        Steps:
        1. Count lost-time accidents (is_lost_time = 1) per month
        2. Count active employees
        3. Calculate hours: heures = nb_employees × 166
        4. Calculate LTIR: LTIR = (nb_accidents × 1,000,000) / heures
        
        Args:
            db: Database session
            year: Year to calculate LTIR for (default: current year)
        
        Returns:
            LTIRDetailResponse with monthly LTIR data
        """
        # Default to current year if not provided
        if year is None:
            year = datetime.now().year
        
        # Get count of active employees (constant for all months)
        nb_active_employees = WorkAccidentService.get_active_employees_count(db)
        
        # Calculate hours worked (constant for all months)
        hours_worked = WorkAccidentService.calculate_hours_worked(nb_active_employees)
        
        # Calculate LTIR for each month
        monthly_data = []
        monthly_ltirs = []
        
        for month in range(1, 13):
            # Count lost-time accidents for this month
            nb_accidents = WorkAccidentService.get_lost_time_accidents_by_month(
                db, month, year
            )
            
            # Calculate LTIR
            ltir = WorkAccidentService.calculate_ltir(nb_accidents, hours_worked)
            monthly_ltirs.append(ltir)
            
            # Format month string
            month_str = f"{year:04d}-{month:02d}"
            
            # Add to monthly data
            monthly_data.append(
                LTIRMonthlyResponse(
                    month=month_str,
                    nb_accidents=nb_accidents,
                    nb_active_employees=nb_active_employees,
                    hours_worked=hours_worked,
                    ltir=ltir
                )
            )
        
        # Calculate average LTIR for the year
        average_ltir = (
            sum(monthly_ltirs) / len(monthly_ltirs)
            if monthly_ltirs else 0.0
        )
        
        return LTIRDetailResponse(
            year=year,
            monthly_data=monthly_data,
            average_ltir=average_ltir
        )
