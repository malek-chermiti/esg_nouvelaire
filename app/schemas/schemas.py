from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class AnomalyBase(BaseModel):
    """Base schema for anomaly data"""
    kpi_id: int
    detected_value: Decimal
    expected_value: Optional[Decimal]
    z_score: Optional[Decimal]
    severity: str
    status: Optional[str] = "NEW"
    date_detected: Optional[datetime]
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class AnomalyResponse(AnomalyBase):
    """Response schema for anomaly with ID"""
    id: int


class AnomalyCreate(BaseModel):
    """Schema for creating a new anomaly"""
    kpi_id: int
    detected_value: Decimal
    expected_value: Optional[Decimal]
    z_score: Optional[Decimal]
    severity: str
    description: Optional[str]


class AnomalyUpdate(BaseModel):
    """Schema for updating anomaly status"""
    status: str