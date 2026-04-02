from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional, List
from decimal import Decimal


class FuelSurchargeMonthlyScoreResponse(BaseModel):
    """Schema for monthly Fuel Surcharge KPI score"""
    month: str  # Format: "YYYY-MM"
    total_amount_tnd: float
    kpi_target: float
    score: float  # (total_amount_tnd / kpi_target) * 100
    
    @field_validator('total_amount_tnd', 'kpi_target', 'score', mode='before')
    @classmethod
    def round_decimals(cls, v):
        """Round decimal values to 3 decimal places"""
        if v is None:
            return v
        # Convert to float and round to 3 decimal places
        float_val = float(v)
        return round(float_val, 3)
    
    class Config:
        from_attributes = True


class FuelSurchargeKpiDetailResponse(BaseModel):
    """Schema for detailed Fuel Surcharge KPI information"""
    kpi_code: str
    kpi_name: str
    unit: str
    monthly_scores: list[FuelSurchargeMonthlyScoreResponse]
    
    class Config:
        from_attributes = True
