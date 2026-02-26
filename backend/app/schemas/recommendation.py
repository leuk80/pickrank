import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RecommendationRead(BaseModel):
    id: uuid.UUID
    episode_id: uuid.UUID
    ticker: str
    company_name: str | None
    type: Literal["BUY", "HOLD", "SELL"]
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    sentence: str | None
    recommendation_date: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationList(BaseModel):
    items: list[RecommendationRead]
    total: int
    page: int
    page_size: int
