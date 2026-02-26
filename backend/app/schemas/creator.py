import uuid
from datetime import datetime

from pydantic import BaseModel


class CreatorBase(BaseModel):
    name: str
    platform: str
    rss_url: str | None = None
    youtube_channel_id: str | None = None
    language: str = "de"


class CreatorCreate(CreatorBase):
    pass


class CreatorScoreEmbedded(BaseModel):
    total_picks: int
    hit_rate: float | None
    avg_outperformance: float | None
    overall_score: float | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreatorRead(CreatorBase):
    id: uuid.UUID
    created_at: datetime
    score: CreatorScoreEmbedded | None = None

    model_config = {"from_attributes": True}


class CreatorList(BaseModel):
    items: list[CreatorRead]
    total: int
