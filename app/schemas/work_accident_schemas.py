from pydantic import BaseModel, field_validator
from typing import List


class LTIRMonthlyResponse(BaseModel):
    """Schema for monthly LTIR calculation"""
    month: str  # Format: "YYYY-MM"
    nb_accidents: int  # Number of lost-time accidents
    nb_active_employees: int  # Number of active employees
    hours_worked: float  # Total hours (employees × 166)
    ltir: float  # Lost Time Injury Rate = (accidents × 1,000,000) / hours
    
    @field_validator('hours_worked', 'ltir', mode='before')
    @classmethod
    def round_decimals(cls, v):
        """Round decimal values to 2 decimal places"""
        if v is None:
            return v
        return round(float(v), 2)
    
    class Config:
        from_attributes = True


class LTIRDetailResponse(BaseModel):
    """Schema for detailed LTIR information"""
    year: int
    monthly_data: list[LTIRMonthlyResponse]
    average_ltir: float  # Average LTIR for the year
    
    @field_validator('average_ltir', mode='before')
    @classmethod
    def round_average(cls, v):
        """Round average to 2 decimal places"""
        if v is None:
            return v
        return round(float(v), 2)
    
    class Config:
        from_attributes = True
