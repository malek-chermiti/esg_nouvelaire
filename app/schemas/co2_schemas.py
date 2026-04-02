from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional, List
from decimal import Decimal


class Co2MonthlyScoreResponse(BaseModel):
    """Schema for monthly CO2 KPI score"""
    month: str  # Format: "YYYY-MM"
    total_co2_kg: float
    kpi_target: float
    score: float  # (total_co2_kg / kpi_target) * 100
    
    @field_validator('total_co2_kg', 'kpi_target', 'score', mode='before')
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


class Co2KpiDetailResponse(BaseModel):
    """Schema for detailed CO2 KPI information"""
    kpi_code: str
    kpi_name: str
    unit: str
    monthly_scores: list[Co2MonthlyScoreResponse]
    
    class Config:
        from_attributes = True


class Co2ByRouteResponse(BaseModel):
    """Schema for CO2 consumption by route"""
    route: str
    co2_tonnes: float
    
    @field_validator('co2_tonnes', mode='before')
    @classmethod
    def round_tonnes(cls, v):
        """Round tonnes to 3 decimal places"""
        if v is None:
            return v
        return round(float(v), 3)
    
    class Config:
        from_attributes = True


class Co2RouteConsumptionResponse(BaseModel):
    """Schema for CO2 consumption by routes"""
    title: str
    unit: str
    total_co2_tonnes: float
    by_route: List[Co2ByRouteResponse]
    
    @field_validator('total_co2_tonnes', mode='before')
    @classmethod
    def round_total(cls, v):
        """Round total to 3 decimal places"""
        if v is None:
            return v
        return round(float(v), 3)
    
    class Config:
        from_attributes = True
