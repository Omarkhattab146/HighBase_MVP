from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class RecommendationRequest(BaseModel):
    customer_id: str | None = None
    business_type: str | None = None
    query: str = ""
    limit: int = Field(5, ge=1, le=20)
    max_price: float | None = Field(None, gt=0)

class Recommendation(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    currency: str
    availability: str
    product_url: str
    score: float
    reasons: list[str]
    evidence: dict[str, float | str] = Field(default_factory=dict)

class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation]
    source: str = "synthetic_demo_data"

class Offer(BaseModel):
    offer_price: float = Field(gt=0)
    discount_percent: float = Field(ge=0, le=100)
    valid_until: str
    eligibility: str = "public"
    description: str

class ProductFact(BaseModel):
    product_id: str
    name: str
    category: str
    price: float | None = Field(None, gt=0)
    currency: str = "BHD"
    availability: str
    stock_quantity: int | None = Field(None, ge=0)
    product_url: str | None = None
    offer: Offer | None = None
    trend_growth: float | None = None
    trend_label: str | None = None

class CustomerIntent(BaseModel):
    kind: str
    query: str = ""
    category: str | None = None
    limit: int = Field(5, ge=1, le=20)
    max_price: float | None = Field(None, gt=0)
    needs_clarification: bool = False

class ChatRequest(RecommendationRequest):
    message: str = ""
    session_id: str | None = None

class ChatResponse(RecommendationResponse):
    response: str
    request_id: str
    data_disclaimer: str = "Recommendations use synthetic demo data."
    session_id: str = ""
    tools_used: list[str] = Field(default_factory=list)
    intent: str = "conversation"
    products: list[ProductFact] = Field(default_factory=list)
    offers: list[ProductFact] = Field(default_factory=list)
    trends: list[ProductFact] = Field(default_factory=list)
    needs_clarification: bool = False

class SessionResponse(BaseModel):
    session_id: str

class DatabaseOverview(BaseModel):
    collections: dict[str, int]
    storage_backend: str

class QualityReport(BaseModel):
    processed: int = 0
    cleaned: int = 0
    rejected: int = 0
    duplicates: int = 0
    missing: int = 0
    outliers: int = 0

class PipelineRun(BaseModel):
    run_id: str
    pipeline_version: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    source_counts: dict[str, int] = Field(default_factory=dict)
    cleaned_counts: dict[str, int] = Field(default_factory=dict)
    stage_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    rejected_ids: list[str] = Field(default_factory=list)

class PipelineResponse(BaseModel):
    run: PipelineRun
    quality: QualityReport
    eda: dict[str, Any]

class DataStore:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]):
        self.collections = collections
        self.metadata: dict[str, Any] = {}
