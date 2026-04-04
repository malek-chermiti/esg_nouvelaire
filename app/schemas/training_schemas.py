from pydantic import BaseModel, field_validator
from typing import List


class TrainingHoursByQuarter(BaseModel):
    """Schema for training hours by quarter"""
    quarter: str  # Format: "Q1 2024", "Q2 2024", etc.
    total_hours: float
    
    @field_validator('total_hours', mode='before')
    @classmethod
    def round_hours(cls, v):
        """Round hours to 2 decimal places"""
        if v is None:
            return v
        return round(float(v), 2)
    
    class Config:
        from_attributes = True


class TrainingHoursPerQuarterResponse(BaseModel):
    """Schema for training hours per quarter response"""
    year: int
    total_hours_year: float
    quarters: List[TrainingHoursByQuarter]
    
    @field_validator('total_hours_year', mode='before')
    @classmethod
    def round_total_hours(cls, v):
        """Round total hours to 2 decimal places"""
        if v is None:
            return v
        return round(float(v), 2)
    
    class Config:
        from_attributes = True
