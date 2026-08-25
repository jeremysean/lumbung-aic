from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str
    issue: str


class ProblemDetails(BaseModel):
    type: str
    title: str
    status: int
    code: str
    trace_id: str
    details: list[ErrorDetail] = Field(default_factory=list)


class HealthData(BaseModel):
    status: Literal["ok"]
    model_version: str


class HealthEnvelope(BaseModel):
    data: HealthData


class RecommendationItem(BaseModel):
    sku_id: str
    category: str
    decision: Literal["BELI_SEKARANG", "TUNDA"]
    order_qty: int
    moq: int
    unit_cost: float
    order_cost: float
    stock_on_hand: float
    on_order: float
    horizon_days: int
    forecast_p50: float
    forecast_p90: float
    stockout_risk: float = Field(ge=0, le=1)
    priority_score: float
    reason: str


class RecommendationAudit(BaseModel):
    model_version: str
    parameter_version: str
    data_cutoff: str
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    review_period_days: int = Field(ge=1)


class RecommendationResult(BaseModel):
    budget: float = Field(gt=0)
    proposed_spend: float = Field(ge=0)
    budget_utilization: float = Field(ge=0, le=1)
    items: list[RecommendationItem]
    audit: RecommendationAudit


class ResponseMeta(BaseModel):
    trace_id: str


class RecommendationEnvelope(BaseModel):
    data: RecommendationResult
    meta: ResponseMeta

