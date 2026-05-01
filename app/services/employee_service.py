from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from decimal import Decimal

from app.models.models import Employee, Kpi, Anomaly
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

    @staticmethod
    def detect_parity_anomalies(db: Session):
        """
        Detect anomalies in gender parity (PARITE_HF).
        
        Compares global_female_percentage to kpi_target.
        Creates anomalies if actual value is below target by more than 5%.
        Direction: HIGHER (anomaly if actual < target)
        
        Args:
            db: Database session
        """
        
        # Get KPI details
        kpi = db.query(Kpi).filter(Kpi.code == "PARITE_HF").first()
        if not kpi:
            raise ValueError("KPI with code PARITE_HF not found")
        
        # Get gender statistics
        gender_stats = EmployeeService.get_gender_stats_by_department(db)
        detected_value = Decimal(str(gender_stats.global_female_percentage))
        expected_value = Decimal(str(kpi.target)) if kpi.target is not None else Decimal(0)

        # Calculate gap percentage: ((target - actual) / target) * 100 for HIGHER direction
        if expected_value > 0:
            gap = ((expected_value - detected_value) / expected_value) * 100
        else:
            gap = Decimal(0)

        # Check if gap exceeds 5% threshold (HIGHER direction: anomaly if actual < target)
        matched_anomalies = []
        seen_anomaly_ids = set()
        period_token = str(datetime.now().year)

        if gap > Decimal(5):
            # Determine severity
            if gap > 20:
                severity = "critique"
            elif gap > 10:
                severity = "haute"
            else:
                severity = "moyenne"
            
            # Calculate z-score (using default std_dev = 5.0)
            std_dev = Decimal("5.0")
            z_score = (detected_value - expected_value) / std_dev if std_dev > 0 else Decimal(0)

            # Create anomaly description
            description = (
                f"Écart de {float(gap):.1f}% sous le seuil de parité H/F pour la période {period_token} "
                f"(cible: {float(expected_value):.1f}%, actuel: {float(detected_value):.1f}%)"
            )
            
            # Check if anomaly already exists for this KPI
            existing_anomaly = db.query(Anomaly).filter(
                Anomaly.kpi_id == kpi.id,
                Anomaly.description.like(f"%{period_token}%")
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
