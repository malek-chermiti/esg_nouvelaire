from pydantic import BaseModel, field_validator
from typing import List


class GenderCountByDepartment(BaseModel):
    """Schema for gender count by department"""
    department: str
    female_count: int
    male_count: int
    total_count: int
    female_percentage: float
    male_percentage: float
    
    @field_validator('female_percentage', 'male_percentage', mode='before')
    @classmethod
    def round_percentage(cls, v):
        """Round percentage to 2 decimal places"""
        if v is None:
            return v
        return round(float(v), 2)
    
    class Config:
        from_attributes = True


class EmployeeGenderStatsResponse(BaseModel):
    """Schema for detailed gender statistics response"""
    total_employees: int
    total_female: int
    total_male: int
    global_female_percentage: float
    global_male_percentage: float
    by_department: List[GenderCountByDepartment]
    
    @field_validator('global_female_percentage', 'global_male_percentage', mode='before')
    @classmethod
    def round_percentage(cls, v):
        """Round percentage to 2 decimal places"""
        if v is None:
            return v
        return round(float(v), 2)
    
    class Config:
        from_attributes = True




