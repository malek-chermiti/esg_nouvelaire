from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional, List
from decimal import Decimal


class WasteRecyclingRateMonthlyResponse(BaseModel):
    """Schema for monthly Waste Management recycling rate"""
    month: str  # Format: "YYYY-MM"
    total_weight_kg: float
    recycled_weight_kg: float
    recycling_rate: float  # (recycled_weight_kg / total_weight_kg) * 100
    kpi_target: float
    score: float  # (recycling_rate / kpi_target) * 100
    
    @field_validator('total_weight_kg', 'recycled_weight_kg', 'recycling_rate', 'kpi_target', 'score', mode='before')
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


class WasteRecyclingRateKpiDetailResponse(BaseModel):
    """Schema for detailed Waste Management recycling rate KPI"""
    kpi_code: str
    kpi_name: str
    unit: str
    monthly_scores: list[WasteRecyclingRateMonthlyResponse]
    
    class Config:
        from_attributes = True
