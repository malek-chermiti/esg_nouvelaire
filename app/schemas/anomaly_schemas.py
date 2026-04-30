from pydantic import BaseModel
from datetime import datetime
from typing import List
from decimal import Decimal


class AnomalyCreate(BaseModel):
    kpi_id: int
    detected_value: float | Decimal
    expected_value: float | Decimal | None = None
    severity: str
    z_score: float | Decimal | None = None
    status: str | None = None
    date_detected: datetime | None = None
    description: str | None = None


class AnomalyResponse(BaseModel):
    id: int
    kpi_id: int
    detected_value: float | Decimal
    expected_value: float | Decimal | None = None
    severity: str
    z_score: float | Decimal | None = None
    status: str | None = None
    date_detected: datetime | None = None
    description: str | None = None
    
    class Config:
        from_attributes = True


class AnomalyListResponse(BaseModel):
    total: int
    anomalies: List[AnomalyResponse]


class AnomalyCriticalResponse(BaseModel):
    total_critical: int
    anomalies: List[AnomalyResponse]
