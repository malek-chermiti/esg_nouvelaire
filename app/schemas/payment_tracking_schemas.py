from pydantic import BaseModel, field_validator
from typing import List


class PaymentModeAmount(BaseModel):
    """Schema for payment by mode in a period"""
    payment_mode: str
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


class PaymentTrackingPeriodResponse(BaseModel):
    """Schema for monthly payment tracking data"""
    period: str  # Format: "YYYY-MM"
    payments_by_mode: list[PaymentModeAmount]
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


class PaymentTrackingResponse(BaseModel):
    """Schema for detailed payment tracking information"""
    periods: list[PaymentTrackingPeriodResponse]
    
    class Config:
        from_attributes = True
