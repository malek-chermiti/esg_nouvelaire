from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.employee_service import EmployeeService
from app.schemas.employee_schemas import EmployeeGenderStatsResponse


router = APIRouter(
    prefix="/api/employees",
    tags=["Employees"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/gender-stats",
    response_model=EmployeeGenderStatsResponse,
    summary="Get gender statistics by department",
    description="Calculate and retrieve gender statistics (female and male count) for all departments"
)
def get_gender_stats_by_department(
    active_only: bool = Query(True, description="Filter only active employees"),
    db: Session = Depends(get_db)
):
    """
    Get detailed gender statistics by department.
    
    - **active_only**: Filter only active employees (default: True)
    - **Returns**: Total employees, female/male counts, percentages, and breakdown by department
    
    Example response:
    ```
    {
        "total_employees": 150,
        "total_female": 60,
        "total_male": 90,
        "global_female_percentage": 40.0,
        "global_male_percentage": 60.0,
        "by_department": [
            {
                "department": "IT",
                "female_count": 10,
                "male_count": 30,
                "total_count": 40,
                "female_percentage": 25.0,
                "male_percentage": 75.0
            }
        ]
    }
    ```
    """
    try:
        return EmployeeService.get_gender_stats_by_department(
            db=db,
            is_active_only=active_only
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
