from pydantic import BaseModel, field_validator
from typing import List


class LicenseTypeAmount(BaseModel):
    """Schema for license cost by type in a period"""
    license_type: str
    total_cost: float
    
    @field_validator('total_cost', mode='before')
    @classmethod
    def round_cost(cls, v):
        """Round cost to 3 decimal places"""
        if v is None:
            return v
        return round(float(v), 3)
    
    class Config:
        from_attributes = True


class AviationLicensePeriodResponse(BaseModel):
    """Schema for monthly aviation license data"""
    period: str  # Format: "YYYY-MM"
    licenses_by_type: list[LicenseTypeAmount]
    total_period: float  # Total for the period
    
    @field_validator('total_period', mode='before')
    @classmethod
    def round_total(cls, v):
        """Round total to 3 decimal places"""
        if v is None:
            return v
        return round(float(v), 3)
    
    class Config:
        from_attributes = True


class AviationLicenseResponse(BaseModel):
    """Schema for detailed aviation license information"""
    year: int
    periods: list[AviationLicensePeriodResponse]
    
    class Config:
        from_attributes = True
