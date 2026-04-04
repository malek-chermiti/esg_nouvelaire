from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Employee
from app.schemas.employee_schemas import (
    GenderCountByDepartment,
    EmployeeGenderStatsResponse
)


class EmployeeService:
    """Service for employee management and statistics"""

    @staticmethod
    def get_gender_stats_by_department(
        db: Session,
        is_active_only: bool = True
    ) -> EmployeeGenderStatsResponse:
        """
        Calculate gender statistics by department.
        
        Args:
            db: Database session
            is_active_only: Filter only active employees (default: True)
        
        Returns:
            EmployeeGenderStatsResponse with gender statistics by department
        """
        
        # Build base query
        query = db.query(Employee)
        if is_active_only:
            query = query.filter(Employee.is_active == 1)
        
        # Get total counts
        total_employees = query.count()
        total_female = query.filter(Employee.gender == 'F').count()
        total_male = query.filter(Employee.gender == 'M').count()
        
        # Calculate global percentages
        global_female_percentage = (total_female / total_employees * 100) if total_employees > 0 else 0
        global_male_percentage = (total_male / total_employees * 100) if total_employees > 0 else 0
        
        # Get statistics by department
        department_stats = db.query(
            Employee.department,
            func.sum(func.if_(Employee.gender == 'F', 1, 0)).label('female_count'),
            func.sum(func.if_(Employee.gender == 'M', 1, 0)).label('male_count'),
            func.count(Employee.id).label('total_count')
        )
        
        if is_active_only:
            department_stats = department_stats.filter(Employee.is_active == 1)
        
        department_stats = department_stats.group_by(Employee.department).all()
        
        # Build department list with percentages
        by_department = []
        for dept_stat in department_stats:
            dept = dept_stat[0]
            female_count = dept_stat[1] or 0
            male_count = dept_stat[2] or 0
            total_count = dept_stat[3] or 0
            
            female_pct = (female_count / total_count * 100) if total_count > 0 else 0
            male_pct = (male_count / total_count * 100) if total_count > 0 else 0
            
            by_department.append(
                GenderCountByDepartment(
                    department=dept,
                    female_count=female_count,
                    male_count=male_count,
                    total_count=total_count,
                    female_percentage=female_pct,
                    male_percentage=male_pct
                )
            )
        
        return EmployeeGenderStatsResponse(
            total_employees=total_employees,
            total_female=total_female,
            total_male=total_male,
            global_female_percentage=global_female_percentage,
            global_male_percentage=global_male_percentage,
            by_department=by_department
        )
