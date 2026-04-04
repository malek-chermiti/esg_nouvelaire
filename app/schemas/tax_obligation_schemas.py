from pydantic import BaseModel, field_validator
from typing import List


class TaxTypeAmount(BaseModel):
    """Schema for tax amount by type in a period"""
    tax_type: str
    total_amount: float
    
    @field_validator('total_amount', mode='before')
    @classmethod
    def round_amount(cls, v):
        """Round amount to 3 decimal places"""
        if v is None:
            return v
        return round(float(v), 3)
    
    class Config:
        from_attributes = True


class TaxObligationPeriodResponse(BaseModel):
    """Schema for monthly tax obligation data"""
    period: str  # Format: "YYYY-MM"
    taxes_by_type: list[TaxTypeAmount]
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


class TaxObligationResponse(BaseModel):
    """Schema for detailed tax obligation information"""
    year: int
    periods: list[TaxObligationPeriodResponse]
    
    class Config:
        from_attributes = True
