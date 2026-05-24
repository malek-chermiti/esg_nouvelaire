from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


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

    @field_serializer("detected_value", "expected_value", "z_score", when_used="json")
    def serialize_decimal_fields(self, value):
        if value is None:
            return None
        quantized = Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        return float(quantized)


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
    status: Literal["RESOLU"]