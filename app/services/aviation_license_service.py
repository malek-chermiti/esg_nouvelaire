from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from typing import List

from app.models.models import AviationLicense
from app.schemas.aviation_license_schemas import (
    AviationLicenseResponse,
    AviationLicensePeriodResponse,
    LicenseTypeAmount
)


class AviationLicenseService:
    """Service for aviation license analysis"""

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
