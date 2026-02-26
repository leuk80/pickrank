import uuid
from datetime import datetime

from pydantic import BaseModel


class RankedCreator(BaseModel):
    rank: int
    creator_id: uuid.UUID
    name: str
    platform: str
    language: str
    total_picks: int
    hit_rate: float | None
    avg_outperformance: float | None
    overall_score: float | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class RankingResponse(BaseModel):
    items: list[RankedCreator]
    total: int
    minimum_picks_required: int = 20
