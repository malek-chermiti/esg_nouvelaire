from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.training_service import TrainingService
from app.schemas.training_schemas import TrainingHoursPerQuarterResponse


router = APIRouter(
    prefix="/api/training",
    tags=["Training"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/hours-per-quarter/{year}",
    response_model=TrainingHoursPerQuarterResponse,
    summary="Get training hours by quarter",
    description="Calculate total training hours for each quarter of a given year"
)
def get_training_hours_per_quarter(
    year: int = Path(..., description="Year", ge=2000, le=2100),
    db: Session = Depends(get_db)
):
    """
    Get total training hours by quarter for a specific year.
    
    - **year**: Year to analyze (required, between 2000 and 2100)
    - **Returns**: Total hours for Q1, Q2, Q3, Q4 with yearly total
    
    Quarters:
    - Q1: January - March
    - Q2: April - June
    - Q3: July - September
    - Q4: October - December
    
    Example response:
    ```
    {
        "year": 2024,
        "total_hours_year": 240.5,
        "quarters": [
            {
                "quarter": "Q1 2024",
                "total_hours": 60.0
            },
            {
                "quarter": "Q2 2024",
                "total_hours": 65.5
            },
            {
                "quarter": "Q3 2024",
                "total_hours": 55.0
            },
            {
                "quarter": "Q4 2024",
                "total_hours": 60.0
            }
        ]
    }
    ```
    """
    try:
        # Validate year
        TrainingService.validate_year(year)
        
        # Get data
        return TrainingService.get_training_hours_per_quarter(db=db, year=year)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
