from pydantic import BaseModel
from typing import List
from decimal import Decimal


class KpiScoreDetail(BaseModel):
    """KPI score detail in pillar response"""
    code: str
    realized: float
    target: float
    score_kpi: float
    weight: float


class PillarScoreResponse(BaseModel):
    """Response for individual pillar score"""
    pillar: str
    score: float
    weight: float
    kpis: List[KpiScoreDetail]


class PillarDetailScore(BaseModel):
    """Pillar detail for global score"""
    score: float
    weight: float


class GlobalScoreResponse(BaseModel):
    """Response for global score"""
    score_global: float
    details: dict  # {"environnement": {...}, "social": {...}, "gouvernance": {...}}
